import pytest

from config import settings
from models.user import User
from models.job import Job
from services.jobs_service import list_jobs
from schemas.resume import UserPreferencesPatch
from services.resume_service import (
    analyze_resume_for_user,
    get_onboarding_status_for_user,
    get_resume_for_user,
    update_preferences_for_user,
    upload_resume_for_user,
)


@pytest.mark.asyncio
async def test_upload_inherits_prefs_version_and_storage(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "openrouter_api_key", None)

    db_session.add(User(id="user_r1", email="r1@example.com"))
    await db_session.commit()

    prof = await upload_resume_for_user(
        db_session, "user_r1", b"%PDF-1.4 fake", "My Resume.pdf", "application/pdf"
    )
    assert prof.version == 1
    assert prof.file_name.endswith("pdf")
    assert prof.parsed_profile.summary
    assert (tmp_path / "user_r1").is_dir()

    got = await get_resume_for_user(db_session, "user_r1")
    assert got is not None and got.id == prof.id

    prof2 = await upload_resume_for_user(
        db_session, "user_r1", b"%PDF-1.4 second", "v2.pdf", "application/pdf"
    )
    assert prof2.version == 2
    assert prof2.preferences.target_role == ""

    patched = await update_preferences_for_user(
        db_session, "user_r1", UserPreferencesPatch(target_role="Backend Engineer", location="EU")
    )
    assert patched.target_role == "Backend Engineer"
    assert patched.location == "EU"

    text = await analyze_resume_for_user(db_session, "user_r1")
    assert "Backend Engineer" in text
    assert "EU" in text


@pytest.mark.asyncio
async def test_preferences_requires_resume(db_session):
    db_session.add(User(id="user_r2", email="r2@example.com"))
    await db_session.commit()

    with pytest.raises(LookupError):
        await update_preferences_for_user(db_session, "user_r2", UserPreferencesPatch(location="US"))


@pytest.mark.asyncio
async def test_onboarding_status_states(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    db_session.add(User(id="user_onb_1", email="onb1@example.com"))
    await db_session.commit()

    status0 = await get_onboarding_status_for_user(db_session, "user_onb_1")
    assert status0.state == "no_resume"
    assert status0.has_resume is False
    assert status0.first_jobs_ready is False

    await upload_resume_for_user(
        db_session, "user_onb_1", b"%PDF-1.4 fake", "resume.pdf", "application/pdf"
    )
    status1 = await get_onboarding_status_for_user(db_session, "user_onb_1")
    assert status1.state == "scoring_in_progress"
    assert status1.has_resume is True
    assert status1.first_jobs_ready is False
    assert status1.eta_seconds is not None and status1.eta_seconds > 0

    db_session.add(
        Job(
            id="jb_onb_001",
            source="catalog",
            external_id="onb-001",
            title="Onboarding Test Role",
            company="Northwind",
            location="Remote",
            salary_range=None,
            description="Test",
            url="https://example.com/onb",
            score_template={
                "fit_score": 4.2,
                "fit_reasons": ["Strong match"],
                "risk_flags": [],
                "dimension_scores": {
                    "tech": 4.5,
                    "culture": 4.0,
                    "seniority": 4.0,
                    "comp": 4.0,
                    "location": 4.5,
                    "channel_recommendation": "email",
                },
            },
        )
    )
    await db_session.commit()
    _ = await list_jobs(db_session, "user_onb_1", min_fit=0.0, location=None, page=1, per_page=20)

    status2 = await get_onboarding_status_for_user(db_session, "user_onb_1")
    assert status2.state == "ready"
    assert status2.first_jobs_ready is True
