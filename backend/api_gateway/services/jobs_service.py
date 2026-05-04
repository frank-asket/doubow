from datetime import datetime, timezone
from uuid import uuid4
import logging
import math
import re

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.job import Job
from models.job_dismissal import JobDismissal
from models.job_score import JobScore
from models.resume import Resume
from schemas.jobs import JobsListResponse, JobWithScore
from services.jobs_cache import (
    get_cached_jobs_list,
    invalidate_user_jobs_list_cache,
    jobs_list_cache_key,
    set_cached_jobs_list,
)
from services.job_score_mapping import job_score_to_api
from services.semantic_match_service import (
    SemanticMatcherUnavailableError,
    keyword_fit_score,
    semantic_fit_score,
)
from services.llm_job_match_service import llm_fit_signal
from services.metrics import observe_matching_blend_score_sync

_ALLOWED_JOB_SOURCES = {
    "ashby",
    "greenhouse",
    "lever",
    "linkedin",
    "wellfound",
    "manual",
    "catalog",
    "adzuna",
    "google_jobs",
}
logger = logging.getLogger(__name__)

# Clamp outcome-driven deltas to avoid extreme personalization (see job_search_feedback).
_MAX_BLEND_DELTA = 0.15


def effective_matching_weights_from_preferences(preferences: dict | None) -> tuple[float, float, float]:
    """Return (semantic, lexical, llm) weights after applying ``feedback_learning.matching_blend_hints``.

    Global settings remain the baseline; stored hints add small per-user nudges for rescoring.
    """
    base_sem = max(0.0, min(1.0, float(settings.semantic_matching_weight)))
    base_lex = max(0.0, min(1.0, float(settings.lexical_matching_weight)))
    base_llm = max(0.0, min(1.0, float(settings.llm_job_matching_weight)))

    hints: dict = {}
    prefs = preferences or {}
    fl = prefs.get("feedback_learning")
    if isinstance(fl, dict):
        mb = fl.get("matching_blend_hints")
        if isinstance(mb, dict):
            hints = mb

    def _delta(key: str) -> float:
        try:
            v = float(hints.get(key) or 0.0)
        except (TypeError, ValueError):
            return 0.0
        return max(-_MAX_BLEND_DELTA, min(_MAX_BLEND_DELTA, v))

    sem = max(0.0, min(1.0, base_sem + _delta("semantic_matching_delta")))
    lex = max(0.0, min(1.0, base_lex + _delta("lexical_matching_delta")))
    llm = max(0.0, min(1.0, base_llm + _delta("llm_job_matching_delta")))
    return sem, lex, llm


def matching_blend_weight_preview(preferences: dict | None) -> dict[str, dict[str, float]]:
    """Human-facing breakdown for APIs (base vs effective weights)."""
    base = {
        "semantic": max(0.0, min(1.0, float(settings.semantic_matching_weight))),
        "lexical": max(0.0, min(1.0, float(settings.lexical_matching_weight))),
        "llm": max(0.0, min(1.0, float(settings.llm_job_matching_weight))),
    }
    sem, lex, llm = effective_matching_weights_from_preferences(preferences)
    return {
        "base": base,
        "effective": {"semantic": sem, "lexical": lex, "llm": llm},
    }


def matching_blend_preview_is_personalized(preview: dict[str, dict[str, float]]) -> bool:
    """True when stored hints change any weight vs global settings (float-safe)."""
    for k in ("semantic", "lexical", "llm"):
        if not math.isclose(preview["base"][k], preview["effective"][k], rel_tol=0.0, abs_tol=1e-9):
            return True
    return False


def _preferences_have_feedback_learning(prefs: dict | None) -> bool:
    if not isinstance(prefs, dict):
        return False
    return isinstance(prefs.get("feedback_learning"), dict)


def _safe_job_source(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_JOB_SOURCES else "manual"


def _location_tokens(raw: str | None) -> list[str]:
    normalized = re.sub(r"[^a-z0-9]+", " ", (raw or "").lower())
    tokens = [token for token in normalized.split() if len(token) >= 2]
    return list(dict.fromkeys(tokens))


def _row_to_schema(job: Job, score_row: JobScore) -> JobWithScore:
    score = job_score_to_api(job.id, score_row)
    if score is None:
        raise ValueError("invalid_job_score_payload")
    return JobWithScore(
        id=job.id,
        source=_safe_job_source(job.source),  # type: ignore[arg-type]
        external_id=job.external_id,
        title=job.title,
        company=job.company,
        location=job.location or "Remote",
        salary_range=job.salary_range,
        logo_url=job.logo_url,
        description_raw=job.description_raw or "",
        description_clean=job.description_clean or job.description or job.description_raw or "",
        description=job.description_clean or job.description or job.description_raw or "",
        canonical_url=job.canonical_url or job.url or "",
        url=job.url or job.canonical_url or "",
        posted_at=job.posted_at,
        discovered_at=job.discovered_at,
        score=score,
    )


def _score_spec_from_template(raw: dict | None) -> dict | None:
    if not isinstance(raw, dict):
        return None
    required = ("fit_score", "fit_reasons", "risk_flags", "dimension_scores")
    if not all(k in raw for k in required):
        return None
    return raw


def _template_provenance(fit_reasons: list[str]) -> str:
    low = [r.lower() for r in fit_reasons]
    if any("imported via discovery" in r for r in low):
        return "template_default"
    return "template_seeded"


async def _sync_template_scores_for_user(
    session: AsyncSession,
    user_id: str,
    *,
    force_recompute: bool = False,
) -> int:
    """Create or refresh template-backed job_scores for a user.

    - default: only create missing scores (keep existing)
    - force_recompute=True: delete existing score rows for template-backed, non-dismissed jobs then recreate
    """
    stmt = select(Job).where(Job.score_template.isnot(None))
    jobs_with_templates = (await session.execute(stmt)).scalars().all()
    if not jobs_with_templates:
        return

    catalog_ids = [j.id for j in jobs_with_templates]
    dismissed_rows = (
        await session.execute(
            select(JobDismissal.job_id).where(JobDismissal.user_id == user_id, JobDismissal.job_id.in_(catalog_ids))
        )
    ).all()
    dismissed = {r[0] for r in dismissed_rows}
    eligible_job_ids = [jid for jid in catalog_ids if jid not in dismissed]

    scored_rows = (
        await session.execute(select(JobScore.job_id).where(JobScore.user_id == user_id, JobScore.job_id.in_(catalog_ids)))
    ).all()
    scored = {r[0] for r in scored_rows}

    if force_recompute and eligible_job_ids:
        await session.execute(
            delete(JobScore).where(
                JobScore.user_id == user_id,
                JobScore.job_id.in_(eligible_job_ids),
            )
        )
        scored = set()

    latest_resume = (
        await session.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc(), Resume.version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    parsed_profile = latest_resume.parsed_profile if latest_resume is not None else None
    prefs_dict = latest_resume.preferences if latest_resume is not None else None
    semantic_weight, lexical_weight, llm_weight = effective_matching_weights_from_preferences(
        prefs_dict if isinstance(prefs_dict, dict) else None
    )
    semantic_enabled = bool(settings.use_semantic_matching and semantic_weight > 0.0)
    llm_top_n = max(0, int(settings.llm_job_matching_top_n))
    llm_enabled = bool(
        settings.use_llm_job_matching and llm_weight > 0.0 and llm_top_n > 0 and settings.openrouter_api_key
    )
    preview = matching_blend_weight_preview(prefs_dict if isinstance(prefs_dict, dict) else None)
    has_fl = _preferences_have_feedback_learning(prefs_dict if isinstance(prefs_dict, dict) else None)
    personalized = matching_blend_preview_is_personalized(preview)
    observe_matching_blend_score_sync(has_feedback_learning=has_fl, personalized_blend=personalized)
    if personalized:
        logger.debug(
            "matching blend hints applied user_id=%s base=%s effective=%s",
            user_id,
            preview["base"],
            preview["effective"],
        )

    now = datetime.now(timezone.utc)
    added_scores = 0
    pending_rows: list[dict] = []
    for job in jobs_with_templates:
        if job.id in scored or job.id in dismissed:
            continue
        spec = _score_spec_from_template(job.score_template if isinstance(job.score_template, dict) else None)
        if spec is None:
            continue
        try:
            fit_score = float(spec["fit_score"])
        except (TypeError, ValueError):
            # Corrupt template data should not break listing for all users.
            continue
        fit_reasons_raw = spec.get("fit_reasons")
        fit_reasons = [str(x) for x in fit_reasons_raw] if isinstance(fit_reasons_raw, list) else []
        risk_flags_raw = spec.get("risk_flags")
        risk_flags = [str(x) for x in risk_flags_raw] if isinstance(risk_flags_raw, list) else []
        provenance = _template_provenance(fit_reasons)
        dims_raw = spec.get("dimension_scores") if isinstance(spec.get("dimension_scores"), dict) else {}
        if semantic_enabled:
            try:
                semantic_score = semantic_fit_score(parsed_profile, job)
            except (SemanticMatcherUnavailableError, Exception):
                semantic_score = None
            if semantic_score is not None:
                fit_score = round(((1.0 - semantic_weight) * fit_score) + (semantic_weight * semantic_score), 1)
                fit_reasons = [*fit_reasons, f"Semantic similarity signal: {semantic_score:.1f}/5.0"]
                provenance = "computed"
        elif lexical_weight > 0.0:
            lexical_score = keyword_fit_score(parsed_profile, job)
            if lexical_score is not None:
                fit_score = round(((1.0 - lexical_weight) * fit_score) + (lexical_weight * lexical_score), 1)
                fit_reasons = [*fit_reasons, f"Keyword overlap signal: {lexical_score:.1f}/5.0"]
                provenance = "computed"
        pending_rows.append(
            {
                "job": job,
                "fit_score": fit_score,
                "fit_reasons": fit_reasons,
                "risk_flags": risk_flags,
                "provenance": provenance,
                "dims_raw": dims_raw,
            }
        )

    if llm_enabled and pending_rows:
        top_candidates = sorted(pending_rows, key=lambda row: float(row["fit_score"]), reverse=True)[:llm_top_n]
        for row in top_candidates:
            job = row["job"]
            try:
                llm_score, llm_reasons, llm_risks = await llm_fit_signal(parsed_profile, job)
            except Exception:
                llm_score, llm_reasons, llm_risks = None, [], []
            if llm_score is not None:
                blended = round(((1.0 - llm_weight) * float(row["fit_score"])) + (llm_weight * llm_score), 1)
                row["fit_score"] = blended
                row["provenance"] = "computed"
                if llm_risks:
                    row["risk_flags"] = [
                        *row["risk_flags"],
                        *[f"LLM fit risk: {r}" for r in llm_risks],
                    ]
                if llm_reasons:
                    row["fit_reasons"] = [
                        *row["fit_reasons"],
                        *[f"LLM fit signal: {r}" for r in llm_reasons],
                    ]
                else:
                    row["fit_reasons"] = [*row["fit_reasons"], f"LLM fit signal: {llm_score:.1f}/5.0"]

    for row in pending_rows:
        session.add(
            JobScore(
                id=str(uuid4()),
                user_id=user_id,
                job_id=row["job"].id,
                fit_score=float(row["fit_score"]),
                fit_reasons=list(row["fit_reasons"]),
                risk_flags=list(row["risk_flags"]),
                dimension_scores=row["dims_raw"],
                provenance=str(row["provenance"]),
                scored_at=now,
            )
        )
        added_scores += 1
    await session.commit()
    if added_scores > 0 or force_recompute:
        await invalidate_user_jobs_list_cache(user_id)
    return added_scores


async def recompute_job_scores_for_user(session: AsyncSession, user_id: str) -> int:
    """Force-refresh template-backed scores for a user after resume/profile updates."""
    return await _sync_template_scores_for_user(session, user_id, force_recompute=True)


async def list_jobs(
    session: AsyncSession,
    user_id: str,
    min_fit: float,
    location: str | None,
    page: int,
    per_page: int = 20,
    has_salary: bool = False,
) -> JobsListResponse:
    cache_key = jobs_list_cache_key(
        user_id=user_id,
        min_fit=min_fit,
        location=location,
        has_salary=has_salary,
        page=page,
        per_page=per_page,
    )
    cached = await get_cached_jobs_list(cache_key)
    if cached is not None:
        return cached

    await _sync_template_scores_for_user(session, user_id)

    filters = [JobScore.user_id == user_id, JobScore.fit_score >= min_fit]
    for token in _location_tokens(location):
        filters.append(func.lower(func.coalesce(Job.location, "")).like(f"%{token}%"))
    if has_salary:
        filters.append(func.length(func.trim(func.coalesce(Job.salary_range, ""))) > 0)

    count_stmt = (
        select(func.count())
        .select_from(Job)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(*filters)
    )
    total = (await session.execute(count_stmt)).scalar_one()

    list_stmt = (
        select(Job, JobScore)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(*filters)
        .order_by(JobScore.scored_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    rows = (await session.execute(list_stmt)).all()
    items: list[JobWithScore] = []
    for job, score_row in rows:
        try:
            items.append(_row_to_schema(job, score_row))
        except Exception:
            # Keep /v1/jobs available even when one persisted row is malformed.
            logger.exception("Skipping malformed job payload user=%s job=%s", user_id, job.id)

    response = JobsListResponse(items=items, total=int(total), page=page, per_page=per_page)
    await set_cached_jobs_list(cache_key, response)
    return response


async def dismiss_job_for_user(session: AsyncSession, user_id: str, job_id: str) -> None:
    job = await session.get(Job, job_id)
    if job is None:
        raise LookupError("job_not_found")

    await session.execute(delete(JobScore).where(JobScore.user_id == user_id, JobScore.job_id == job_id))

    existing = (
        await session.execute(
            select(JobDismissal).where(JobDismissal.user_id == user_id, JobDismissal.job_id == job_id)
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(JobDismissal(user_id=user_id, job_id=job_id))

    await session.commit()
    await invalidate_user_jobs_list_cache(user_id)
