"""Resume-derived catalog ingest parameters."""

import pytest

from models.resume import Resume
from models.user import User
from services.provider_adapter import ProviderFetchParams
from services.resume_catalog_params import merge_catalog_params_with_resume, provider_params_from_user_resume


@pytest.mark.asyncio
async def test_provider_params_from_resume_composes_keywords(db_session):
    uid = "user_rcp"
    db_session.add(User(id=uid, email="rcp@example.com"))
    await db_session.commit()
    db_session.add(
        Resume(
            user_id=uid,
            file_name="cv.pdf",
            storage_path="/tmp/x",
            parsed_profile={
                "name": "T",
                "headline": "Backend engineer focus on APIs",
                "skills": ["Python", "Go"],
                "top_skills": ["Python", "PostgreSQL"],
            },
            preferences={"target_role": "Staff Engineer", "location": "Berlin"},
        )
    )
    await db_session.commit()

    p = await provider_params_from_user_resume(db_session, uid)
    assert p is not None
    assert p.keywords
    assert "Staff" in (p.keywords or "") or "Staff Engineer" in (p.keywords or "")
    assert p.location == "Berlin"


@pytest.mark.asyncio
async def test_merge_prefers_resume_when_present(db_session):
    uid = "user_rcp2"
    db_session.add(User(id=uid, email="rcp2@example.com"))
    await db_session.commit()
    db_session.add(
        Resume(
            user_id=uid,
            file_name="cv.pdf",
            storage_path="/tmp/y",
            parsed_profile={"headline": "SRE"},
            preferences={"location": "Lisbon"},
        )
    )
    await db_session.commit()

    base = ProviderFetchParams(keywords="legacy", location="London", country=None, page=2, per_page=30)
    merged = await merge_catalog_params_with_resume(db_session, uid, base)
    assert "SRE" in (merged.keywords or "")
    assert merged.location == "Lisbon"
    assert merged.page == 2
    assert merged.per_page == 30
