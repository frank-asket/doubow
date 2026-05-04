from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.job import Job
from models.job_alert_delivery import JobAlertDelivery
from models.job_alert_subscription import JobAlertSubscription
from models.job_score import JobScore
from models.user import User
from routers import job_alerts
from schemas.job_alerts import JobAlertSettingsPatch
from services import job_alert_service


@pytest.mark.asyncio
async def test_job_alert_settings_roundtrip(db_session: AsyncSession):
    uid = "user_alert_settings_1"
    db_session.add(User(id=uid, email="alerts-settings@example.com"))
    await db_session.commit()

    got = await job_alert_service.get_job_alert_settings(db_session, user_id=uid)
    assert got.enabled is True
    assert got.frequency == "daily"
    assert got.min_fit == 4.0
    assert got.max_items == 5

    patched = await job_alert_service.patch_job_alert_settings(
        db_session,
        user_id=uid,
        payload=JobAlertSettingsPatch(enabled=True, frequency="weekly", min_fit=3.6, max_items=8, email_enabled=True),
    )
    assert patched.frequency == "weekly"
    assert patched.min_fit == 3.6
    assert patched.max_items == 8


@pytest.mark.asyncio
async def test_run_job_alerts_for_user_creates_deliveries_and_updates_last_run(db_session: AsyncSession, monkeypatch):
    uid = "user_alert_send_1"
    now = datetime.now(timezone.utc)
    db_session.add(User(id=uid, email="alerts-send@example.com"))
    db_session.add(
        JobAlertSubscription(
            id="sub_alert_1",
            user_id=uid,
            enabled=True,
            frequency="daily",
            min_fit=4.0,
            max_items=5,
            email_enabled=True,
            last_run_at=now - timedelta(days=1),
        )
    )
    db_session.add(
        Job(
            id="job_alert_1",
            source="catalog",
            external_id="alert-1",
            title="Backend Engineer",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="desc",
            url="https://example.com/j1",
            discovered_at=now - timedelta(hours=1),
        )
    )
    db_session.add(
        JobScore(
            id="score_alert_1",
            user_id=uid,
            job_id="job_alert_1",
            fit_score=4.6,
            fit_reasons=["Strong Python match"],
            risk_flags=[],
            dimension_scores={},
            scored_at=now - timedelta(minutes=10),
            provenance="computed",
        )
    )
    await db_session.commit()

    async def _fake_send_email_outbound(*, to_addr: str, subject: str, body: str) -> bool:
        assert to_addr == "alerts-send@example.com"
        assert "Backend Engineer" in body
        return True

    monkeypatch.setattr(job_alert_service, "send_email_outbound", _fake_send_email_outbound)
    result = await job_alert_service.run_job_alerts_for_user(db_session, user_id=uid, now=now)
    assert result == {"candidates": 1, "sent": 1}

    deliveries = (
        await db_session.execute(select(JobAlertDelivery).where(JobAlertDelivery.user_id == uid))
    ).scalars().all()
    assert len(deliveries) == 1

    sub = (
        await db_session.execute(select(JobAlertSubscription).where(JobAlertSubscription.user_id == uid))
    ).scalar_one()
    assert sub.last_run_at is not None


@pytest.mark.asyncio
async def test_run_job_alerts_send_failure_does_not_advance_last_run(db_session: AsyncSession, monkeypatch):
    uid = "user_alert_send_fail_1"
    now = datetime.now(timezone.utc)
    last_run = now - timedelta(days=1)
    db_session.add(User(id=uid, email="alerts-send-fail@example.com"))
    db_session.add(
        JobAlertSubscription(
            id="sub_alert_fail_1",
            user_id=uid,
            enabled=True,
            frequency="daily",
            min_fit=4.0,
            max_items=5,
            email_enabled=True,
            last_run_at=last_run,
        )
    )
    db_session.add(
        Job(
            id="job_alert_fail_1",
            source="catalog",
            external_id="alert-fail-1",
            title="Platform Engineer",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="desc",
            url="https://example.com/fail-1",
            discovered_at=now - timedelta(hours=1),
        )
    )
    db_session.add(
        JobScore(
            id="score_alert_fail_1",
            user_id=uid,
            job_id="job_alert_fail_1",
            fit_score=4.7,
            fit_reasons=["Great platform fit"],
            risk_flags=[],
            dimension_scores={},
            scored_at=now - timedelta(minutes=10),
            provenance="computed",
        )
    )
    await db_session.commit()

    async def _fake_send_email_outbound(*, to_addr: str, subject: str, body: str) -> bool:
        return False

    monkeypatch.setattr(job_alert_service, "send_email_outbound", _fake_send_email_outbound)
    result = await job_alert_service.run_job_alerts_for_user(db_session, user_id=uid, now=now)
    assert result == {"candidates": 1, "sent": 0}

    sub = (
        await db_session.execute(select(JobAlertSubscription).where(JobAlertSubscription.user_id == uid))
    ).scalar_one()
    assert sub.last_run_at is not None
    assert sub.last_run_at.replace(tzinfo=timezone.utc) == last_run


@pytest.mark.asyncio
async def test_get_or_create_subscription_recovers_from_unique_race():
    user_id = "user_alert_race_1"
    existing = JobAlertSubscription(id="sub_existing", user_id=user_id)

    class _Result:
        def __init__(self, row):
            self._row = row

        def scalar_one_or_none(self):
            return self._row

    class _DummySession:
        def __init__(self):
            self._rows = [None, existing]
            self.rolled_back = False

        async def execute(self, *_args, **_kwargs):
            return _Result(self._rows.pop(0))

        def add(self, *_args, **_kwargs):
            return None

        async def commit(self):
            raise IntegrityError("INSERT", {}, Exception("duplicate key value"))

        async def rollback(self):
            self.rolled_back = True

        async def refresh(self, *_args, **_kwargs):
            return None

    session = _DummySession()
    row = await job_alert_service._get_or_create_subscription(session, user_id)
    assert row is existing
    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_list_job_alert_feed_returns_historical_items(db_session: AsyncSession):
    uid = "user_alert_feed_1"
    now = datetime.now(timezone.utc)
    db_session.add(User(id=uid, email="alerts-feed@example.com"))
    db_session.add(
        Job(
            id="job_alert_feed_1",
            source="catalog",
            external_id="alert-feed-1",
            title="Staff Engineer",
            company="Globex",
            location="Remote",
            salary_range=None,
            description="desc",
            url="https://example.com/feed-1",
            discovered_at=now - timedelta(days=1),
        )
    )
    db_session.add(
        JobScore(
            id="score_alert_feed_1",
            user_id=uid,
            job_id="job_alert_feed_1",
            fit_score=4.4,
            fit_reasons=["Strong backend systems"],
            risk_flags=["Domain ramp-up"],
            dimension_scores={},
            scored_at=now - timedelta(hours=12),
            provenance="computed",
        )
    )
    db_session.add(
        JobAlertDelivery(
            id="delivery_alert_feed_1",
            user_id=uid,
            subscription_id=None,
            job_id="job_alert_feed_1",
            fit_score=4.4,
            delivered_at=now - timedelta(hours=2),
        )
    )
    await db_session.commit()

    out = await job_alert_service.list_job_alert_feed(db_session, user_id=uid, page=1, per_page=20)
    assert out.total == 1
    assert len(out.items) == 1
    item = out.items[0]
    assert item.delivery_id == "delivery_alert_feed_1"
    assert item.job_id == "job_alert_feed_1"
    assert item.title == "Staff Engineer"
    assert item.fit_reasons == ["Strong backend systems"]
    assert item.risk_flags == ["Domain ramp-up"]


def test_job_alert_settings_endpoints(monkeypatch):
    app = FastAPI()
    app.include_router(job_alerts.router, prefix="/v1")

    async def _override_authenticated_user() -> User:
        return User(id="user_alert_api_1", email="alerts-api@example.com")

    class _DummySession:
        pass

    async def _override_session():
        yield _DummySession()

    app.dependency_overrides[get_authenticated_user] = _override_authenticated_user
    app.dependency_overrides[get_session] = _override_session

    async def _get_settings(*, session, user_id):  # type: ignore[no-untyped-def]
        return {"enabled": True, "frequency": "daily", "min_fit": 4.0, "max_items": 5, "email_enabled": True, "last_run_at": None}

    async def _patch_settings(*, session, user_id, payload):  # type: ignore[no-untyped-def]
        return {"enabled": bool(payload.enabled), "frequency": payload.frequency or "daily", "min_fit": 3.5, "max_items": 7, "email_enabled": True, "last_run_at": None}

    async def _feed(*, session, user_id, page, per_page):  # type: ignore[no-untyped-def]
        return {"items": [], "total": 0, "page": page, "per_page": per_page}

    monkeypatch.setattr("routers.job_alerts.get_job_alert_settings", _get_settings)
    monkeypatch.setattr("routers.job_alerts.patch_job_alert_settings", _patch_settings)
    monkeypatch.setattr("routers.job_alerts.list_job_alert_feed", _feed)

    c = TestClient(app)
    got = c.get("/v1/me/job-alerts/settings")
    assert got.status_code == 200
    assert got.json()["frequency"] == "daily"

    upd = c.put("/v1/me/job-alerts/settings", json={"enabled": True, "frequency": "weekly"})
    assert upd.status_code == 200
    assert upd.json()["frequency"] == "weekly"

    feed = c.get("/v1/me/job-alerts/feed?page=1&per_page=10")
    assert feed.status_code == 200
    assert feed.json()["total"] == 0
