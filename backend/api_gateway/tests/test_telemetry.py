from datetime import UTC, datetime, timedelta

import pytest

from models.user import User
from schemas.telemetry import TelemetryEventIn
from services import telemetry_service
from services.telemetry_service import get_activation_kpi, record_event


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
