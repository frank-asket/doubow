"""Autopilot scopes: failed_only and gmail_failed_only resolve from prior run item_results."""

import pytest
from datetime import datetime, timezone

from models.application import Application
from models.autopilot_run import AutopilotRun
from models.job import Job
from models.user import User
from services.autopilot_runner import (
    _gmail_failed_application_ids_from_results,
    _resolve_target_application_ids,
)


def test_gmail_failed_extracts_errors_with_hints():
    items = [
        {"application_id": "a1", "status": "failed", "error": "Gmail API 403"},
        {"application_id": "a2", "status": "failed", "error": "timeout"},
        {"application_id": "a3", "status": "success"},
    ]
    assert _gmail_failed_application_ids_from_results(items) == ["a1"]


@pytest.mark.asyncio
async def test_resolve_failed_only_from_prior_run(db_session):
    uid = "user_scope_1"
    db_session.add(User(id=uid, email="scope@example.com"))
    jid = "job_scope_1"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="s1",
            title="T",
            company="C",
            location="R",
            description="d",
            url="https://example.com/j",
        )
    )
    await db_session.commit()
    db_session.add_all(
        [
            Application(id="app_ok", user_id=uid, job_id=jid, status="pending", channel="email"),
            Application(id="app_bad", user_id=uid, job_id=jid, status="pending", channel="email"),
        ]
    )
    done_at = datetime.now(timezone.utc)
    db_session.add(
        AutopilotRun(
            id="run_prior_1",
            user_id=uid,
            status="done",
            scope="all",
            idempotency_key="idem_prior_12345678",
            request_fingerprint="fp1",
            item_results=[
                {
                    "application_id": "app_ok",
                    "status": "success",
                    "retryable": False,
                    "latency_ms": 1,
                    "error": None,
                },
                {
                    "application_id": "app_bad",
                    "status": "failed",
                    "retryable": True,
                    "latency_ms": 2,
                    "error": "boom",
                },
            ],
            completed_at=done_at,
        )
    )
    await db_session.commit()

    ids = await _resolve_target_application_ids(
        db_session,
        user_id=uid,
        scope="failed_only",
        application_ids=None,
    )
    assert ids == ["app_bad"]


@pytest.mark.asyncio
async def test_resolve_gmail_failed_only_filters_by_error(db_session):
    uid = "user_scope_2"
    db_session.add(User(id=uid, email="scope2@example.com"))
    jid = "job_scope_2"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="s2",
            title="T",
            company="C",
            location="R",
            description="d",
            url="https://example.com/j",
        )
    )
    await db_session.commit()
    db_session.add_all(
        [
            Application(id="g1", user_id=uid, job_id=jid, status="pending", channel="email"),
            Application(id="g2", user_id=uid, job_id=jid, status="pending", channel="email"),
        ]
    )
    db_session.add(
        AutopilotRun(
            id="run_prior_2",
            user_id=uid,
            status="done",
            scope="all",
            idempotency_key="idem_prior_22345678",
            request_fingerprint="fp2",
            item_results=[
                {"application_id": "g1", "status": "failed", "error": "oauth token revoked", "latency_ms": 1},
                {"application_id": "g2", "status": "failed", "error": "random failure", "latency_ms": 1},
            ],
            completed_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    ids = await _resolve_target_application_ids(
        db_session,
        user_id=uid,
        scope="gmail_failed_only",
        application_ids=None,
    )
    assert ids == ["g1"]
