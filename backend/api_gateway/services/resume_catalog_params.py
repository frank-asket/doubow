"""Derive catalog ingest search parameters from a user's latest resume + preferences."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume
from schemas.resume import ParsedProfileModel, UserPreferencesModel
from services.provider_adapter import ProviderFetchParams
from services.resume_service import merge_preferences_dicts, normalize_parsed_profile_dict

_KEYWORD_MAX_LEN = 220


def _dedupe_preserve(parts: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        low = p.lower()
        if low not in seen:
            seen.add(low)
            out.append(p)
    return out


def _compose_keyword_query(parsed: ParsedProfileModel, prefs: UserPreferencesModel) -> str:
    parts: list[str] = []
    tr = (prefs.target_role or "").strip()
    if tr:
        parts.append(tr)
    hl = (parsed.headline or "").strip()
    if hl:
        parts.append(hl)
    skills = list(parsed.top_skills or []) or list(parsed.skills or [])
    for s in skills[:10]:
        st = str(s).strip()
        if st:
            parts.append(st)
    merged = _dedupe_preserve(parts)
    text = " ".join(merged).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > _KEYWORD_MAX_LEN:
        text = text[:_KEYWORD_MAX_LEN].rsplit(" ", 1)[0].strip()
    return text


async def provider_params_from_user_resume(
    session: AsyncSession, user_id: str
) -> ProviderFetchParams | None:
    """Return fetch params when the user has at least one resume row."""
    row = (
        await session.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc(), Resume.version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        return None

    parsed = ParsedProfileModel.model_validate(normalize_parsed_profile_dict(row.parsed_profile or {}))
    prefs = UserPreferencesModel.model_validate(merge_preferences_dicts(row.preferences, {}))
    keywords = _compose_keyword_query(parsed, prefs)
    location = (prefs.location or "").strip() or None
    if not keywords and not location:
        return ProviderFetchParams(keywords=None, location=None, country=None, page=1, per_page=50)
    return ProviderFetchParams(
        keywords=keywords or None,
        location=location,
        country=None,
        page=1,
        per_page=50,
        posted_after=None,
    )


async def merge_catalog_params_with_resume(
    session: AsyncSession, user_id: str, base: ProviderFetchParams
) -> ProviderFetchParams:
    """Prefer resume-derived keywords/location when present; keep pagination from ``base``."""
    built = await provider_params_from_user_resume(session, user_id)
    if built is None:
        return base
    return ProviderFetchParams(
        keywords=built.keywords or base.keywords,
        location=built.location or base.location,
        country=built.country or base.country,
        page=base.page,
        per_page=base.per_page,
        posted_after=base.posted_after,
    )
