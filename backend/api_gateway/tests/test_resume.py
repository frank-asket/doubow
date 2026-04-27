import pytest
from pathlib import Path

from config import settings
from models.user import User
from models.job import Job
from models.job_score import JobScore
from services.jobs_service import list_jobs
from schemas.resume import UserPreferencesPatch
from services.resume_service import (
    analyze_resume_for_user,
    get_onboarding_status_for_user,
    get_resume_for_user,
    update_preferences_for_user,
    upload_resume_for_user,
)
from services.langchain_resume_analysis import LangChainUnavailableError


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


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_file_type(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    db_session.add(User(id="user_bad_type", email="badtype@example.com"))
    await db_session.commit()

    with pytest.raises(ValueError, match="Unsupported file type"):
        await upload_resume_for_user(
            db_session,
            "user_bad_type",
            b"plain text",
            "resume.txt",
            "text/plain",
        )


@pytest.mark.asyncio
async def test_upload_rejects_empty_file(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    db_session.add(User(id="user_empty", email="empty@example.com"))
    await db_session.commit()

    with pytest.raises(ValueError, match="Uploaded file is empty"):
        await upload_resume_for_user(
            db_session,
            "user_empty",
            b"",
            "resume.pdf",
            "application/pdf",
        )


@pytest.mark.asyncio
async def test_upload_parser_failure_returns_validation_error(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    db_session.add(User(id="user_parse_fail", email="parsefail@example.com"))
    await db_session.commit()

    async def _boom(*args, **kwargs):
        raise RuntimeError("parser exploded")

    monkeypatch.setattr("services.resume_service.parse_resume", _boom)
    with pytest.raises(ValueError, match="Failed to parse resume content"):
        await upload_resume_for_user(
            db_session,
            "user_parse_fail",
            b"%PDF-1.4 fake",
            "resume.pdf",
            "application/pdf",
        )


@pytest.mark.asyncio
async def test_upload_storage_write_failure_returns_validation_error(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    db_session.add(User(id="user_write_fail", email="writefail@example.com"))
    await db_session.commit()

    original_write_bytes = Path.write_bytes

    def _fail_write(self, data):  # type: ignore[no-untyped-def]
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_bytes", _fail_write)
    try:
        with pytest.raises(ValueError, match="Failed to persist uploaded resume"):
            await upload_resume_for_user(
                db_session,
                "user_write_fail",
                b"%PDF-1.4 fake",
                "resume.pdf",
                "application/pdf",
            )
    finally:
        monkeypatch.setattr(Path, "write_bytes", original_write_bytes)


@pytest.mark.asyncio
async def test_analyze_resume_uses_langchain_when_flag_enabled(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "openrouter_api_key", "or_test_key")
    monkeypatch.setattr(settings, "use_langchain", True)
    db_session.add(User(id="user_lc", email="lc@example.com"))
    await db_session.commit()

    await upload_resume_for_user(
        db_session, "user_lc", b"%PDF-1.4 fake", "resume.pdf", "application/pdf"
    )

    async def _lc(*args, **kwargs):
        return "Summary: LangChain analysis"

    monkeypatch.setattr("services.resume_service.analyze_resume_with_langchain", _lc)
    out = await analyze_resume_for_user(db_session, "user_lc")
    assert out == "Summary: LangChain analysis"


@pytest.mark.asyncio
async def test_analyze_resume_langchain_failure_falls_back(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "openrouter_api_key", "or_test_key")
    monkeypatch.setattr(settings, "use_langchain", True)
    db_session.add(User(id="user_lc_fallback", email="lcf@example.com"))
    await db_session.commit()

    await upload_resume_for_user(
        db_session, "user_lc_fallback", b"%PDF-1.4 fake", "resume.pdf", "application/pdf"
    )

    async def _boom(*args, **kwargs):
        raise RuntimeError("lc fail")

    monkeypatch.setattr("services.resume_service.analyze_resume_with_langchain", _boom)
    out = await analyze_resume_for_user(db_session, "user_lc_fallback")
    assert "Profile:" in out


@pytest.mark.asyncio
async def test_upload_resume_triggers_score_recompute(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "use_semantic_matching", False)
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.5)

    uid = "user_resume_recompute_1"
    db_session.add(User(id=uid, email="rr1@example.com"))
    db_session.add(
        Job(
            id="jb_resume_recompute_1",
            source="catalog",
            external_id="resume-recompute-1",
            title="Senior AI Product Engineer",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="Build ML platform and LLM features",
            url="https://example.com/recompute",
            score_template={
                "fit_score": 4.0,
                "fit_reasons": ["ok"],
                "risk_flags": [],
                "dimension_scores": {
                    "tech": 4.0,
                    "culture": 4.0,
                    "seniority": 4.0,
                    "comp": 4.0,
                    "location": 4.0,
                    "channel_recommendation": "email",
                },
            },
        )
    )
    db_session.add(
        JobScore(
            id="score_resume_stale_1",
            user_id=uid,
            job_id="jb_resume_recompute_1",
            fit_score=4.0,
            fit_reasons=["stale"],
            risk_flags=[],
            dimension_scores={
                "tech": 4.0,
                "culture": 4.0,
                "seniority": 4.0,
                "comp": 4.0,
                "location": 4.0,
                "channel_recommendation": "email",
            },
        )
    )
    await db_session.commit()

    async def _parse_resume(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "name": "Jane Doe",
            "headline": "School Administrator",
            "experience_years": 9,
            "skills": ["curriculum", "administration", "operations", "communication"],
            "top_skills": ["curriculum", "administration", "operations"],
            "archetypes": [],
            "gaps": [],
            "summary": "Led student operations and policy compliance.",
        }

    monkeypatch.setattr("services.resume_service.parse_resume", _parse_resume)
    await upload_resume_for_user(db_session, uid, b"%PDF-1.4 fake", "resume.pdf", "application/pdf")

    listing = await list_jobs(db_session, uid, min_fit=0.0, location=None, page=1, per_page=20)
    assert listing.total == 1
    item = listing.items[0]
    assert item.score.fit_score < 4.0
    assert any("Keyword overlap signal" in r for r in item.score.fit_reasons)


@pytest.mark.asyncio
async def test_analyze_resume_langchain_unavailable_falls_back(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "openrouter_api_key", "or_test_key")
    monkeypatch.setattr(settings, "use_langchain", True)
    db_session.add(User(id="user_lc_missing_dep", email="lcmissing@example.com"))
    await db_session.commit()

    await upload_resume_for_user(
        db_session, "user_lc_missing_dep", b"%PDF-1.4 fake", "resume.pdf", "application/pdf"
    )

    async def _missing(*args, **kwargs):
        raise LangChainUnavailableError("langchain-core is not installed")

    monkeypatch.setattr("services.resume_service.analyze_resume_with_langchain", _missing)
    out = await analyze_resume_for_user(db_session, "user_lc_missing_dep")
    assert "Profile:" in out
