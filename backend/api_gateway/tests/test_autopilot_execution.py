"""Autopilot runner executes draft creation per application."""

import pytest

from models.application import Application
from models.autopilot_run import AutopilotRun
from models.job import Job
from models.user import User
from sqlalchemy import select

import services.autopilot_runner as autopilot_runner
from workflow.autopilot_langgraph import AutopilotGraphState, run_autopilot_via_langgraph


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

    await autopilot_runner._execute_autopilot_body(
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


@pytest.mark.asyncio
async def test_langgraph_and_legacy_produce_identical_item_results(db_session, monkeypatch):
    uid = "user_auto_2"
    db_session.add(User(id=uid, email="auto2@example.com"))
    jid = "job_auto_2"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="auto-j-2",
            title="Role",
            company="Co",
            location="Remote",
            description="d",
            url="https://example.com/j",
        )
    )
    await db_session.commit()

    app_ok = "app_auto_ok"
    app_fail = "app_auto_fail"
    db_session.add_all(
        [
            Application(id=app_ok, user_id=uid, job_id=jid, status="pending", channel="email"),
            Application(id=app_fail, user_id=uid, job_id=jid, status="pending", channel="email"),
        ]
    )
    db_session.add_all(
        [
            AutopilotRun(
                id="run_legacy_parity",
                user_id=uid,
                status="queued",
                scope="all",
                idempotency_key="idem_legacy_parity",
                request_fingerprint="fp_legacy_parity",
            ),
            AutopilotRun(
                id="run_langgraph_parity",
                user_id=uid,
                status="queued",
                scope="all",
                idempotency_key="idem_langgraph_parity",
                request_fingerprint="fp_langgraph_parity",
            ),
        ]
    )
    await db_session.commit()

    async def _draft_stub(_session, _user_id: str, app_id: str):
        if app_id == app_fail:
            raise RuntimeError("forced failure for parity test")
        return None

    monkeypatch.setattr(autopilot_runner, "create_draft_approval_for_application", _draft_stub)

    def _set_perf_counter_sequence():
        values = iter([10.0, 10.011, 20.0, 20.021])
        monkeypatch.setattr(autopilot_runner.time, "perf_counter", lambda: next(values))

    _set_perf_counter_sequence()
    await autopilot_runner._execute_autopilot_body(
        db_session,
        run_id="run_legacy_parity",
        user_id=uid,
        application_ids=[app_ok, app_fail],
    )

    _set_perf_counter_sequence()
    await run_autopilot_via_langgraph(
        initial_state=AutopilotGraphState(
            run_id="run_langgraph_parity",
            user_id=uid,
            application_ids=[app_ok, app_fail],
        ),
        mark_running=lambda state: autopilot_runner._langgraph_mark_running_step(
            session=db_session,
            state=state,
        ),
        resolve_targets=lambda state: autopilot_runner._langgraph_resolve_targets_step(
            session=db_session,
            state=state,
        ),
        process_items=lambda state: autopilot_runner._langgraph_process_items_step(
            session=db_session,
            state=state,
        ),
        persist_done=lambda state: autopilot_runner._langgraph_persist_done_step(
            session=db_session,
            state=state,
        ),
        persist_failed=lambda state: autopilot_runner._langgraph_persist_failed_step(
            session=db_session,
            state=state,
        ),
    )

    legacy = (
        await db_session.execute(select(AutopilotRun).where(AutopilotRun.id == "run_legacy_parity"))
    ).scalar_one()
    langgraph = (
        await db_session.execute(select(AutopilotRun).where(AutopilotRun.id == "run_langgraph_parity"))
    ).scalar_one()

    assert legacy.status == "done"
    assert langgraph.status == "done"
    assert legacy.item_results == langgraph.item_results


@pytest.mark.asyncio
async def test_persist_run_failed_stores_structured_failure_metadata(db_session):
    uid = "user_auto_failure_1"
    db_session.add(User(id=uid, email="auto-failure@example.com"))
    run = AutopilotRun(
        id="run_failed_metadata_001",
        user_id=uid,
        status="running",
        scope="all",
        idempotency_key="idem_failed_metadata",
        request_fingerprint="fp_failed_metadata",
    )
    db_session.add(run)
    await db_session.commit()

    await autopilot_runner._persist_run_failed(
        db_session,
        run_id="run_failed_metadata_001",
        error_code="resolve_targets_failed",
        error_detail="database timeout while resolving targets",
        failed_node="resolve_targets",
    )

    row = (
        await db_session.execute(select(AutopilotRun).where(AutopilotRun.id == "run_failed_metadata_001"))
    ).scalar_one()
    assert row.status == "failed"
    assert row.failure_code == "resolve_targets_failed"
    assert row.failure_detail == "database timeout while resolving targets"
    assert row.failure_node == "resolve_targets"
