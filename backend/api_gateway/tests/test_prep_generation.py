"""Prep session generation persists rows and returns nested application payloads."""

import pytest

from models.application import Application
from models.job import Job
from models.user import User
from services.prep_assist_service import generate_prep_assist_text
from services.prep_service import PrepApplicationNotFoundError, generate_prep_for_application, get_prep_detail_for_user


@pytest.mark.asyncio
async def test_generate_prep_creates_session_and_get_returns_detail(db_session):
    uid = "user_prep_gen"
    db_session.add(User(id=uid, email="prep@example.com"))
    jid = "job_prep_gen"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="prep-j",
            title="Backend Engineer",
            company="Acme Labs",
            location="Remote",
            description="Build APIs",
            url="https://example.com/job",
        )
    )
    await db_session.commit()
    aid = "app_prep_gen"
    db_session.add(Application(id=aid, user_id=uid, job_id=jid, status="pending", channel="email"))
    await db_session.commit()

    detail = await generate_prep_for_application(db_session, uid, aid)
    assert detail.id.startswith("prep_")
    assert detail.application.id == aid
    assert len(detail.questions) >= 1
    assert detail.company_brief
    assert detail.star_stories
    assert detail.star_stories[0].get("confidence") in {"low", "medium", "high"}

    loaded = await get_prep_detail_for_user(db_session, uid, aid)
    assert loaded is not None
    assert loaded.id == detail.id


@pytest.mark.asyncio
async def test_prep_assist_unknown_application_raises(db_session):
    uid = "user_prep_assist_missing"
    db_session.add(User(id=uid, email="miss@example.com"))
    await db_session.commit()

    with pytest.raises(PrepApplicationNotFoundError):
        await generate_prep_assist_text(db_session, uid, "app_does_not_exist", "company_brief")
