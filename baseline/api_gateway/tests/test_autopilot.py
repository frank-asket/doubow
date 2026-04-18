from sqlalchemy import select
import pytest

from models.autopilot_run import AutopilotRun
from schemas.autopilot import AutopilotRunRequest
from services.autopilot_service import run_autopilot


@pytest.mark.asyncio
async def test_autopilot_persists_and_replays(db_session):
    payload = AutopilotRunRequest(scope="all", application_ids=["app_1"])

    created, replayed = await run_autopilot(
        session=db_session,
        user_id="user_1",
        idempotency_key="idem_abc12345",
        payload=payload,
    )
    assert replayed is False
    assert created.status == "queued"
    assert created.replayed is False

    replay, replayed = await run_autopilot(
        session=db_session,
        user_id="user_1",
        idempotency_key="idem_abc12345",
        payload=payload,
    )
    assert replayed is True
    assert replay.replayed is True
    assert replay.run_id == created.run_id

    rows = (await db_session.execute(select(AutopilotRun))).scalars().all()
    assert len(rows) == 1
    assert rows[0].idempotency_key == "idem_abc12345"


@pytest.mark.asyncio
async def test_autopilot_conflict_on_same_key_different_payload(db_session):
    first_payload = AutopilotRunRequest(scope="all", application_ids=["app_1"])
    second_payload = AutopilotRunRequest(scope="failed_only", application_ids=["app_2"])

    await run_autopilot(
        session=db_session,
        user_id="user_2",
        idempotency_key="idem_conflict_123",
        payload=first_payload,
    )

    try:
        await run_autopilot(
            session=db_session,
            user_id="user_2",
            idempotency_key="idem_conflict_123",
            payload=second_payload,
        )
        assert False, "Expected ValueError for idempotency payload conflict"
    except ValueError as exc:
        assert str(exc)


@pytest.mark.asyncio
async def test_autopilot_same_idempotency_key_different_users(db_session):
    payload = AutopilotRunRequest(scope="all", application_ids=["app_1"])
    key = "idem_shared_across_users_12"

    a, replay_a = await run_autopilot(
        session=db_session, user_id="user_a", idempotency_key=key, payload=payload
    )
    b, replay_b = await run_autopilot(
        session=db_session, user_id="user_b", idempotency_key=key, payload=payload
    )
    assert replay_a is False and replay_b is False
    assert a.run_id != b.run_id

    rows = (await db_session.execute(select(AutopilotRun))).scalars().all()
    assert len(rows) == 2
