"""Autopilot runner executes draft creation per application."""

import pytest

from models.application import Application
from models.autopilot_run import AutopilotRun
from models.job import Job
from models.user import User
from sqlalchemy import select

from services.autopilot_runner import _execute_autopilot_body


@pytest.mark.asyncio
async def test_execute_autopilot_generates_item_results(db_session):
    uid = "user_auto_1"
    db_session.add(User(id=uid, email="auto@example.com"))
    jid = "job_auto_1"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="auto-j",
            title="Role",
            company="Co",
            location="Remote",
            description="d",
            url="https://example.com/j",
        )
    )
    await db_session.commit()
    aid = "app_auto_1"
    db_session.add(Application(id=aid, user_id=uid, job_id=jid, status="pending", channel="email"))
    run = AutopilotRun(
        id="run_test_001",
        user_id=uid,
        status="queued",
        scope="all",
        idempotency_key="idem_auto_12345678",
        request_fingerprint="fp",
        started_at=None,
    )
    db_session.add(run)
    await db_session.commit()

    await _execute_autopilot_body(
        db_session,
        run_id="run_test_001",
        user_id=uid,
        application_ids=None,
    )

    run = (
        await db_session.execute(select(AutopilotRun).where(AutopilotRun.id == "run_test_001"))
    ).scalar_one()
    assert run.status == "done"
    assert run.item_results is not None
    assert len(run.item_results) == 1
    assert run.item_results[0]["application_id"] == aid
    assert run.item_results[0]["status"] == "success"
