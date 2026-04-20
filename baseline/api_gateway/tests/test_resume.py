import pytest

from config import settings
from models.user import User
from schemas.resume import UserPreferencesPatch
from services.resume_service import (
    analyze_resume_for_user,
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
