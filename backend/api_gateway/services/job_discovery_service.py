"""Import / upsert jobs into the shared catalog (discovery feed → Postgres)."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus, urlparse
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from schemas.jobs import DiscoverJobsRequest, DiscoverJobsResponse
from services.job_ingestion_sanitizer import normalize_optional_http_url
from services.jobs_service import _sync_template_scores_for_user


def _default_score_template() -> dict:
    return {
        "fit_score": 3.5,
        "fit_reasons": ["Imported via discovery — refine after you review the fit"],
        "risk_flags": [],
        "dimension_scores": {
            "tech": 3.5,
            "culture": 3.5,
            "seniority": 3.5,
            "comp": 3.5,
            "location": 3.5,
            "channel_recommendation": "email",
        },
    }


def _normalize_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.split()).strip()


def _provider_canonical_url(*, source: str, external_id: str, raw_url: str | None, title: str, company: str) -> str:
    safe_raw_url = normalize_optional_http_url(raw_url)
    if safe_raw_url:
        return safe_raw_url
    eid = (external_id or "").strip()
    src = (source or "manual").strip().lower()
    slug = quote_plus(f"{title} {company}".strip())
    if src == "linkedin":
        digits = "".join(ch for ch in eid if ch.isdigit())
        if digits:
            return f"https://www.linkedin.com/jobs/view/{digits}/"
        return f"https://www.linkedin.com/jobs/search/?keywords={slug}"
    if src == "greenhouse":
        return f"https://boards.greenhouse.io/jobs/{quote_plus(eid)}" if eid else f"https://boards.greenhouse.io/?q={slug}"
    if src == "lever":
        return f"https://jobs.lever.co/{quote_plus(eid)}" if eid else f"https://jobs.lever.co/?q={slug}"
    if src == "ashby":
        return f"https://jobs.ashbyhq.com/{quote_plus(eid)}" if eid else f"https://jobs.ashbyhq.com/?q={slug}"
    return f"https://www.google.com/search?q={slug}"


def _validated_logo_url(candidate: str | None, canonical_url: str, company: str) -> str | None:
    safe_candidate = normalize_optional_http_url(candidate)
    if safe_candidate:
        return safe_candidate
    try:
        domain = urlparse(canonical_url).hostname or ""
    except Exception:
        domain = ""
    if not domain or domain in {"example.com", "www.example.com", "google.com", "www.google.com"}:
        safe_company = company.lower().replace(" ", "")
        if not safe_company:
            return None
        return f"https://logo.clearbit.com/{safe_company}.com"
    return f"https://logo.clearbit.com/{domain}"


async def discover_upsert_jobs(
    session: AsyncSession, user_id: str, payload: DiscoverJobsRequest, *, sync_scores: bool = True
) -> DiscoverJobsResponse:
    """Upsert jobs by (source, external_id); sync template-driven scores for this user."""
    created = 0
    updated = 0
    job_ids: list[str] = []

    for item in payload.jobs:
        stmt = select(Job).where(Job.source == item.source, Job.external_id == item.external_id)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        template = item.score_template if isinstance(item.score_template, dict) else _default_score_template()
        description_raw = _normalize_whitespace(item.description_raw or item.description)
        description_clean = _normalize_whitespace(item.description)
        canonical_url = _provider_canonical_url(
            source=item.source,
            external_id=item.external_id,
            raw_url=item.url,
            title=item.title,
            company=item.company,
        )
        logo_url = _validated_logo_url(item.logo_url, canonical_url, item.company)

        if existing is None:
            row = Job(
                id=str(uuid4()),
                source=item.source,
                external_id=item.external_id,
                title=item.title,
                company=item.company,
                location=item.location,
                salary_range=item.salary_range,
                logo_url=logo_url,
                description_raw=description_raw or None,
                description_clean=description_clean or None,
                description=description_clean or description_raw or None,
                canonical_url=canonical_url,
                url=canonical_url,
                posted_at=item.posted_at,
                discovered_at=datetime.now(timezone.utc),
                score_template=template,
            )
            session.add(row)
            await session.flush()
            job_ids.append(row.id)
            created += 1
        else:
            existing.title = item.title
            existing.company = item.company
            existing.location = item.location
            existing.salary_range = item.salary_range
            existing.logo_url = logo_url
            existing.description_raw = description_raw or None
            existing.description_clean = description_clean or None
            existing.description = description_clean or description_raw or None
            existing.canonical_url = canonical_url
            existing.url = canonical_url
            if item.posted_at is not None:
                existing.posted_at = item.posted_at
            existing.score_template = template
            await session.flush()
            job_ids.append(existing.id)
            updated += 1

    await session.commit()

    if sync_scores:
        await _sync_template_scores_for_user(session, user_id)

    return DiscoverJobsResponse(created=created, updated=updated, job_ids=job_ids)
