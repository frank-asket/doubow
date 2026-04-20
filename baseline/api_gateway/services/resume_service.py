import re
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.resume import Resume
from schemas.resume import (
    ParsedProfileModel,
    ResumeProfileResponse,
    UserPreferencesModel,
    UserPreferencesPatch,
)
from services.openrouter import chat_completion
from services.resume_parser import parse_resume


def default_prefs_dict() -> dict:
    return UserPreferencesModel().model_dump()


def _slug_filename(name: str, max_len: int = 120) -> str:
    base = Path(name).name
    base = re.sub(r"[^\w.\-]+", "_", base, flags=re.UNICODE).strip("._") or "resume"
    return base[:max_len]


def normalize_parsed_profile_dict(raw: dict) -> dict:
    skills = list(raw.get("skills") or [])
    top = list(raw.get("top_skills") or skills[:5])
    merged = {
        "name": str(raw.get("name") or ""),
        "headline": str(raw.get("headline") or ""),
        "experience_years": float(raw.get("experience_years") or 0),
        "skills": skills,
        "top_skills": top[:10] if top else skills[:5],
        "archetypes": list(raw.get("archetypes") or []),
        "gaps": list(raw.get("gaps") or []),
        "summary": str(raw.get("summary") or ""),
    }
    ParsedProfileModel.model_validate(merged)
    return merged


def merge_preferences_dicts(stored: dict | None, patch: dict) -> dict:
    base = {**default_prefs_dict(), **(stored or {})}
    for key, value in patch.items():
        if value is not None:
            base[key] = value
    return UserPreferencesModel.model_validate(base).model_dump()


def _seniority_from_experience_years(years: float) -> str:
    """Map total experience years to a coarse seniority bucket."""
    if years < 2:
        return "Junior"
    if years < 5:
        return "Mid"
    if years < 9:
        return "Senior"
    if years < 14:
        return "Lead"
    if years < 20:
        return "Staff"
    return "Principal"


def infer_preferences_from_parsed_profile(parsed: dict) -> dict:
    """Derive preference fields from structured résumé data (best-effort).

    Only emits keys when there is signal in the parsed profile so we do not
    wipe user-edited preferences on re-upload when parsing is empty or stubbed.
    """
    headline = str(parsed.get("headline") or "").strip()
    archetypes = [str(a).strip() for a in (parsed.get("archetypes") or []) if str(a).strip()]
    skills_raw = parsed.get("top_skills") or parsed.get("skills") or []
    skills = [str(s).strip() for s in skills_raw if str(s).strip()]
    years = float(parsed.get("experience_years") or 0)

    has_signal = bool(headline or archetypes or skills or years > 0)

    patch: dict = {}
    if headline:
        patch["target_role"] = headline[:255]
    elif archetypes:
        patch["target_role"] = archetypes[0][:255]

    if skills:
        patch["skills"] = skills[:20]

    if has_signal:
        patch["seniority"] = _seniority_from_experience_years(years)

    return patch


def resume_row_to_response(row: Resume) -> ResumeProfileResponse:
    parsed = normalize_parsed_profile_dict(row.parsed_profile or {})
    prefs = merge_preferences_dicts(row.preferences, {})
    return ResumeProfileResponse(
        id=row.id,
        storage_path=row.storage_path,
        file_name=row.file_name or "",
        parsed_profile=ParsedProfileModel.model_validate(parsed),
        preferences=UserPreferencesModel.model_validate(prefs),
        version=row.version,
        created_at=row.created_at,
    )


async def _get_latest_resume_row(session: AsyncSession, user_id: str) -> Resume | None:
    stmt = (
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc(), Resume.version.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_resume_for_user(session: AsyncSession, user_id: str) -> ResumeProfileResponse | None:
    row = await _get_latest_resume_row(session, user_id)
    if row is None:
        return None
    return resume_row_to_response(row)


async def upload_resume_for_user(
    session: AsyncSession,
    user_id: str,
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
) -> ResumeProfileResponse:
    if len(file_bytes) > 15 * 1024 * 1024:
        raise ValueError("File too large (max 15MB)")

    parsed_raw = await parse_resume(file_bytes, content_type or "application/octet-stream")
    normalized = normalize_parsed_profile_dict(parsed_raw)

    prev = await _get_latest_resume_row(session, user_id)
    next_version = (prev.version + 1) if prev else 1
    prefs_dict = merge_preferences_dicts(prev.preferences if prev else None, {})
    inferred = infer_preferences_from_parsed_profile(normalized)
    prefs_dict = merge_preferences_dicts(prefs_dict, inferred)

    resume_id = str(uuid4())
    safe_name = _slug_filename(filename)
    rel_path = f"{user_id}/{resume_id}_{safe_name}"

    root = Path(settings.resume_storage_dir).expanduser().resolve()
    dest = root / user_id / f"{resume_id}_{safe_name}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(file_bytes)

    row = Resume(
        id=resume_id,
        user_id=user_id,
        file_name=safe_name,
        storage_path=rel_path,
        parsed_profile=normalized,
        preferences=prefs_dict,
        version=next_version,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return resume_row_to_response(row)


async def update_preferences_for_user(
    session: AsyncSession, user_id: str, patch: UserPreferencesPatch
) -> UserPreferencesModel:
    row = await _get_latest_resume_row(session, user_id)
    if row is None:
        raise LookupError("no_resume")

    patch_dict = patch.model_dump(exclude_unset=True)
    merged = merge_preferences_dicts(row.preferences, patch_dict)
    row.preferences = merged
    row.version = row.version + 1
    await session.commit()
    await session.refresh(row)
    return UserPreferencesModel.model_validate(merged)


def build_profile_analysis(profile: ParsedProfileModel, prefs: UserPreferencesModel) -> str:
    lines: list[str] = []
    if profile.name or profile.headline:
        lines.append(f"Profile: {profile.name or 'Unknown'} — {profile.headline or 'No headline yet'}.")
    else:
        lines.append("Profile: headline and name are empty; consider adding a clear professional title.")

    if profile.experience_years:
        lines.append(f"Approximate experience signal: {profile.experience_years:g} years.")
    if profile.skills:
        lines.append(f"Skills surfaced: {', '.join(profile.skills[:12])}.")
    else:
        lines.append("No skills extracted yet — list your core stack so matching can rank roles accurately.")

    if prefs.target_role or prefs.location:
        lines.append(f"Job search targets: role “{prefs.target_role or 'any'}”, location “{prefs.location or 'flexible'}”.")

    if profile.gaps:
        lines.append("Gaps to revisit: " + "; ".join(profile.gaps[:5]) + ".")

    if profile.summary:
        lines.append(f"Summary: {profile.summary}")

    lines.append(
        "Next steps: tighten your headline for your target role, quantify impact in recent roles, "
        "and align listed skills with the stacks you want next."
    )
    return "\n\n".join(lines)


def _openrouter_analysis_prompt(parsed: ParsedProfileModel, prefs: UserPreferencesModel) -> tuple[str, str]:
    system = (
        "You are a concise career coach. Given structured résumé data and job-search preferences, "
        "write a short profile analysis: strengths, gaps, fit for the stated target role/location, "
        "and 3–5 concrete next steps. Use plain text with short paragraphs or bullet lines; no markdown headings."
    )
    user = (
        f"Parsed profile:\n{parsed.model_dump_json(indent=2)}\n\n"
        f"Preferences:\n{prefs.model_dump_json(indent=2)}"
    )
    return system, user


async def analyze_resume_for_user(session: AsyncSession, user_id: str) -> str:
    row = await _get_latest_resume_row(session, user_id)
    if row is None:
        raise LookupError("no_resume")

    parsed = ParsedProfileModel.model_validate(normalize_parsed_profile_dict(row.parsed_profile or {}))
    prefs = UserPreferencesModel.model_validate(merge_preferences_dicts(row.preferences, {}))

    if settings.openrouter_api_key:
        try:
            system, user = _openrouter_analysis_prompt(parsed, prefs)
            return await chat_completion(system_message=system, user_message=user)
        except Exception:
            return build_profile_analysis(parsed, prefs)

    return build_profile_analysis(parsed, prefs)
