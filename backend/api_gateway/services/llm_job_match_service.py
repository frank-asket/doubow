"""Optional LLM-assisted resume/job matching helpers."""

from __future__ import annotations

import json
from typing import Any, Optional

from config import settings
from models.job import Job
from services.openrouter import chat_completion


def _profile_summary(parsed_profile: dict | None) -> str:
    if not isinstance(parsed_profile, dict):
        return ""
    headline = str(parsed_profile.get("headline") or "").strip()
    summary = str(parsed_profile.get("summary") or "").strip()
    skills = [str(s).strip() for s in (parsed_profile.get("skills") or []) if str(s).strip()]
    parts = [p for p in (headline, summary, ", ".join(skills[:30])) if p]
    return "\n".join(parts)


def _job_posting_block(job: Job) -> str:
    return "\n".join(
        p
        for p in (
            f"Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location or 'n/a'}",
            f"Description: {(job.description or job.description_clean or job.description_raw or '')[:5000]}",
        )
        if p
    )


def _extract_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(raw[start : end + 1])
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def _clamp_fit(fit: float | None) -> float | None:
    if fit is None:
        return None
    return max(1.0, min(5.0, float(fit)))


async def _llm_fit_signal_legacy(profile: str, posting: str) -> tuple[float | None, list[str], list[str]]:
    """Single-pass fit JSON (original behaviour), routed via ``use_case=deep`` for model tiering."""
    system = (
        "You are a strict evaluator for resume-job matching. "
        "Output ONLY valid JSON with keys: fit_score (number 1.0-5.0), reasons (array of <=3 short strings). "
        "No markdown."
    )
    user = (
        "Evaluate candidate fit for this job.\n\n"
        f"Resume profile:\n{profile}\n\n"
        f"Job posting:\n{posting}\n\n"
        "Return JSON only."
    )
    raw = await chat_completion(user_message=user, system_message=system, use_case="deep")
    parsed = _extract_json(raw)
    if not parsed:
        return None, [], []

    fit_raw = parsed.get("fit_score")
    try:
        fit = float(fit_raw)
    except (TypeError, ValueError):
        fit = None
    fit = _clamp_fit(fit)

    reasons_raw = parsed.get("reasons")
    reasons = [str(r).strip() for r in reasons_raw] if isinstance(reasons_raw, list) else []
    reasons = [r for r in reasons if r][:3]
    return fit, reasons, []


async def _llm_fit_bull(profile: str, posting: str) -> dict[str, Any] | None:
    system = (
        "You argue FOR why this candidate is a strong match for the job (steel-man the fit). "
        "Output ONLY valid JSON with keys: arguments (array of 2-5 short strings, each one concrete pro-fit point). "
        "Optional key strength (number 1.0-5.0) for how compelling the pro case is. No markdown."
    )
    user = f"Resume profile:\n{profile}\n\nJob posting:\n{posting}\n\nReturn JSON only."
    raw = await chat_completion(user_message=user, system_message=system, use_case="deep")
    return _extract_json(raw)


async def _llm_fit_bear(profile: str, posting: str) -> dict[str, Any] | None:
    system = (
        "You argue AGAINST the match: gaps, risks, or reasons this candidate may struggle or be a poor hire. "
        "Output ONLY valid JSON with keys: concerns (array of 2-5 short strings, each one concrete concern). "
        "Optional key severity (number 1.0-5.0) for how serious the issues are. No markdown."
    )
    user = f"Resume profile:\n{profile}\n\nJob posting:\n{posting}\n\nReturn JSON only."
    raw = await chat_completion(user_message=user, system_message=system, use_case="deep")
    return _extract_json(raw)


async def _llm_fit_synthesis(
    profile: str,
    posting: str,
    bull: dict[str, Any],
    bear: dict[str, Any],
) -> Optional[tuple[float | None, list[str], list[str]]]:
    system = (
        "You integrate a pro/con analysis into one balanced hiring judgment. "
        "Output ONLY valid JSON with keys: fit_score (number 1.0-5.0), "
        "reasons (array of <=3 short strings explaining primary fit), "
        "risk_flags (array of <=3 short strings for material risks or gaps; empty if none). "
        "No markdown."
    )
    user = (
        "Resume profile:\n"
        f"{profile}\n\n"
        "Job posting:\n"
        f"{posting}\n\n"
        "Pro case (JSON):\n"
        f"{json.dumps(bull, ensure_ascii=False)}\n\n"
        "Con case (JSON):\n"
        f"{json.dumps(bear, ensure_ascii=False)}\n\n"
        "Return JSON only."
    )
    raw = await chat_completion(user_message=user, system_message=system, use_case="deep")
    parsed = _extract_json(raw)
    if not parsed:
        return None

    fit_raw = parsed.get("fit_score")
    try:
        fit = float(fit_raw)
    except (TypeError, ValueError):
        fit = None
    fit = _clamp_fit(fit)

    reasons_raw = parsed.get("reasons")
    reasons = [str(r).strip() for r in reasons_raw] if isinstance(reasons_raw, list) else []
    reasons = [r for r in reasons if r][:3]

    risks_raw = parsed.get("risk_flags")
    risks = [str(r).strip() for r in risks_raw] if isinstance(risks_raw, list) else []
    risks = [r for r in risks if r][:3]

    return fit, reasons, risks


async def llm_fit_signal(parsed_profile: dict | None, job: Job) -> tuple[float | None, list[str], list[str]]:
    """Return optional LLM fit score, pro reasons, and risk-style strings.

    Score range must be 1.0-5.0. Returns ``(None, [], [])`` when input is insufficient or parsing fails
    (unless debate steps fall back to legacy single-pass).
    """
    profile = _profile_summary(parsed_profile)
    posting = _job_posting_block(job)
    if not profile or not posting:
        return None, [], []

    if not settings.use_llm_fit_debate:
        return await _llm_fit_signal_legacy(profile, posting)

    try:
        bull = await _llm_fit_bull(profile, posting)
        bear = await _llm_fit_bear(profile, posting)
    except Exception:
        return await _llm_fit_signal_legacy(profile, posting)

    if not bull or not bear:
        return await _llm_fit_signal_legacy(profile, posting)

    args_ok = isinstance(bull.get("arguments"), list) and len(bull.get("arguments") or []) >= 1
    cons_ok = isinstance(bear.get("concerns"), list) and len(bear.get("concerns") or []) >= 1
    if not args_ok or not cons_ok:
        return await _llm_fit_signal_legacy(profile, posting)

    try:
        synthesized = await _llm_fit_synthesis(profile, posting, bull, bear)
    except Exception:
        return await _llm_fit_signal_legacy(profile, posting)

    if not synthesized:
        return await _llm_fit_signal_legacy(profile, posting)

    fit, reasons, risks = synthesized
    if fit is None:
        return await _llm_fit_signal_legacy(profile, posting)
    return fit, reasons, risks
