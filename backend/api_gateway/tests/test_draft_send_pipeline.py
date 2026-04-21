"""Draft generation → approve → stub send durable state."""

import pytest

from models.application import Application
from models.job import Job
from models.user import User
from services.approvals_service import approve_approval
from services.draft_service import create_draft_approval_for_application
from services.send_approval_service import execute_approval_send_stub


@pytest.mark.asyncio
async def test_create_draft_then_approve_then_send_updates_state(db_session):
    uid = "user_pipe_1"
    db_session.add(User(id=uid, email="pipe@example.com"))
    jid = "job_pipe_1"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="ext-p",
            title="Engineer",
            company="Acme",
            location="Remote",
            description="Build things",
            url="https://example.com/job",
        )
    )
    await db_session.commit()

    aid = "app_pipe_1"
    db_session.add(Application(id=aid, user_id=uid, job_id=jid, status="pending", channel="email"))
    await db_session.commit()

    approval_schema = await create_draft_approval_for_application(db_session, uid, aid)
    assert approval_schema.status == "pending"
    assert "Acme" in approval_schema.draft_body or "OPENROUTER" in approval_schema.draft_body

    resp = await approve_approval(db_session, uid, approval_schema.id, edited_body=None, idempotency_key="approve_key_12345678")
    assert resp.queued_send is True
    assert resp.send_task_id

    await execute_approval_send_stub(db_session, approval_schema.id, uid)

    from sqlalchemy import select
    from models.approval import Approval as ApprovalRow

    row = (await db_session.execute(select(ApprovalRow).where(ApprovalRow.id == approval_schema.id))).scalar_one()
    assert row.sent_at is not None

    app_row = await db_session.get(Application, aid)
    assert app_row is not None
    assert app_row.status == "applied"
    assert app_row.applied_at is not None


@pytest.mark.asyncio
async def test_duplicate_draft_returns_existing_pending(db_session):
    uid = "user_pipe_2"
    db_session.add(User(id=uid, email="pipe2@example.com"))
    jid = "job_pipe_2"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="ext-q",
            title="Designer",
            company="Co",
            location="Remote",
            description="d",
            url="https://example.com/q",
        )
    )
    await db_session.commit()
    aid = "app_pipe_2"
    db_session.add(Application(id=aid, user_id=uid, job_id=jid, status="pending", channel="email"))
    await db_session.commit()

    first = await create_draft_approval_for_application(db_session, uid, aid)
    second = await create_draft_approval_for_application(db_session, uid, aid)
    assert first.id == second.id


@pytest.mark.asyncio
async def test_approve_with_edit_preserves_edited_status(db_session):
    uid = "user_pipe_3"
    db_session.add(User(id=uid, email="pipe3@example.com"))
    jid = "job_pipe_3"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="ext-r",
            title="PM",
            company="X",
            location="Remote",
            description="d",
            url="https://example.com/r",
        )
    )
    await db_session.commit()
    aid = "app_pipe_3"
    db_session.add(Application(id=aid, user_id=uid, job_id=jid, status="pending", channel="linkedin"))
    await db_session.commit()

    approval_schema = await create_draft_approval_for_application(db_session, uid, aid)
    resp = await approve_approval(
        db_session,
        uid,
        approval_schema.id,
        edited_body="Edited outreach body for tests.",
        idempotency_key="approve_edit_87654321",
    )
    assert resp.status == "edited"
