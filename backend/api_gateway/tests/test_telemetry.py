from datetime import UTC, datetime, timedelta

import pytest

from models.approval import Approval
from models.application import Application
from models.job import Job
from models.user import User
from schemas.telemetry import TelemetryEventIn
from services import telemetry_service
from services.telemetry_service import get_activation_kpi, get_outcome_kpi, record_event


@pytest.mark.asyncio
async def test_activation_kpi_computes_duration(db_session):
    db_session.add(User(id="user_t1", email="telemetry1@example.com"))
    await db_session.commit()

    start = datetime.now(UTC)
    await record_event(
        db_session,
        "user_t1",
        TelemetryEventIn(event_name="resume_upload_succeeded", occurred_at=start),
    )
    await record_event(
        db_session,
        "user_t1",
        TelemetryEventIn(event_name="first_matches_ready", occurred_at=start + timedelta(seconds=95)),
    )

    kpi = await get_activation_kpi(db_session, "user_t1")
    assert kpi.sample_size == 1
    assert kpi.latest_time_to_first_matches_seconds == 95
    assert kpi.avg_time_to_first_matches_seconds == 95


@pytest.mark.asyncio
async def test_activation_kpi_empty_without_pair(db_session):
    db_session.add(User(id="user_t2", email="telemetry2@example.com"))
    await db_session.commit()

    await record_event(
        db_session,
        "user_t2",
        TelemetryEventIn(event_name="resume_upload_succeeded", occurred_at=datetime.now(UTC)),
    )
    kpi = await get_activation_kpi(db_session, "user_t2")
    assert kpi.sample_size == 0
    assert kpi.latest_time_to_first_matches_seconds is None


@pytest.mark.asyncio
async def test_activation_kpi_prefers_posthog_pairs(monkeypatch, db_session):
    db_session.add(User(id="user_t3", email="telemetry3@example.com"))
    await db_session.commit()

    start = datetime.now(UTC)
    async def _fake_pairs(_user_id: str):
        return [(start, start + timedelta(seconds=60)), (start, start + timedelta(seconds=120))]

    monkeypatch.setattr(
        telemetry_service,
        "fetch_activation_event_pairs",
        _fake_pairs,
    )

    kpi = await get_activation_kpi(db_session, "user_t3")
    assert kpi.sample_size == 2
    assert kpi.latest_time_to_first_matches_seconds == 120
    assert kpi.avg_time_to_first_matches_seconds == 90


@pytest.mark.asyncio
async def test_outcome_kpi_computes_approval_rates(db_session):
    db_session.add(User(id="user_t4", email="telemetry4@example.com"))
    db_session.add(
        Job(
            id="job_t4",
            source="manual",
            external_id="ext_t4",
            title="Role",
            company="Company",
            location="Remote",
            description="desc",
            url="https://example.com/role",
        )
    )
    db_session.add(
        Application(id="app_t4_a", user_id="user_t4", job_id="job_t4", status="saved", channel="email")
    )
    db_session.add(
        Application(id="app_t4_b", user_id="user_t4", job_id="job_t4", status="saved", channel="email")
    )
    db_session.add(
        Application(id="app_t4_c", user_id="user_t4", job_id="job_t4", status="saved", channel="email")
    )
    db_session.add(
        Approval(
            id="ap_t4_pending",
            user_id="user_t4",
            application_id="app_t4_a",
            type="cover_letter",
            channel="email",
            subject="s1",
            draft_body="d1",
            status="pending",
        )
    )
    db_session.add(
        Approval(
            id="ap_t4_approved",
            user_id="user_t4",
            application_id="app_t4_b",
            type="cover_letter",
            channel="email",
            subject="s2",
            draft_body="d2",
            status="approved",
            approved_at=datetime.now(UTC),
            sent_at=datetime.now(UTC),
        )
    )
    db_session.add(
        Approval(
            id="ap_t4_rejected",
            user_id="user_t4",
            application_id="app_t4_c",
            type="cover_letter",
            channel="email",
            subject="s3",
            draft_body="d3",
            status="rejected",
        )
    )
    await db_session.commit()

    kpi = await get_outcome_kpi(db_session, "user_t4")
    assert kpi.approvals_created == 3
    assert kpi.approvals_resolved == 2
    assert kpi.approvals_approved_or_edited == 1
    assert kpi.approvals_sent == 1
    assert kpi.approval_resolution_rate == pytest.approx(2 / 3)
    assert kpi.approval_acceptance_rate == pytest.approx(1 / 3)
    assert kpi.approval_send_rate == pytest.approx(1 / 3)


@pytest.mark.asyncio
async def test_outcome_kpi_handles_empty_user(db_session):
    db_session.add(User(id="user_t5", email="telemetry5@example.com"))
    await db_session.commit()

    kpi = await get_outcome_kpi(db_session, "user_t5")
    assert kpi.approvals_created == 0
    assert kpi.approval_resolution_rate is None
    assert kpi.approval_acceptance_rate is None
    assert kpi.approval_send_rate is None
