"""Optional LLM-assisted resume/job matching helpers."""

from __future__ import annotations

import json
from typing import Any

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


async def llm_fit_signal(parsed_profile: dict | None, job: Job) -> tuple[float | None, list[str]]:
    """Return optional LLM fit score and concise reasons.

    Score range must be 1.0-5.0. Returns (None, []) when input is insufficient.
    """
    profile = _profile_summary(parsed_profile)
    posting = "\n".join(
        p
        for p in (
            f"Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location or 'n/a'}",
            f"Description: {(job.description or job.description_clean or job.description_raw or '')[:5000]}",
        )
        if p
    )
    if not profile or not posting:
        return None, []

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
    raw = await chat_completion(user_message=user, system_message=system, use_case="resume")
    parsed = _extract_json(raw)
    if not parsed:
        return None, []

    fit_raw = parsed.get("fit_score")
    try:
        fit = float(fit_raw)
    except (TypeError, ValueError):
        fit = None
    if fit is not None:
        fit = max(1.0, min(5.0, fit))

    reasons_raw = parsed.get("reasons")
    reasons = [str(r).strip() for r in reasons_raw] if isinstance(reasons_raw, list) else []
    reasons = [r for r in reasons if r][:3]
    return fit, reasons

