"""HTTP tests for profile-impression webhook (minimal FastAPI app, no full ``main`` import)."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from db.session import get_session
from models.user import User
from routers import webhooks


@pytest.fixture
def webhook_app(db_session):
    app = FastAPI()
    app.include_router(webhooks.router, prefix="/v1")

    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    return app


@pytest.mark.asyncio
async def test_profile_impression_webhook_requires_secret(monkeypatch, webhook_app):
    monkeypatch.setattr("routers.webhooks.settings.profile_impression_webhook_secret", "configured-secret")
    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/webhooks/profile-impression", json={"user_id": "x", "count": 1})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_profile_impression_webhook_increments(monkeypatch, webhook_app, db_session):
    monkeypatch.setattr("routers.webhooks.settings.profile_impression_webhook_secret", "configured-secret")

    uid = "user_wh_pv"
    db_session.add(User(id=uid, email="wh@example.com", profile_views=None))
    await db_session.commit()

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/webhooks/profile-impression",
            json={"user_id": uid, "count": 2},
            headers={"X-Webhook-Secret": "configured-secret"},
        )
    assert r.status_code == 200
    assert r.json() == {"profile_views": 2}


@pytest.mark.asyncio
async def test_profile_impression_webhook_404_unknown_user(monkeypatch, webhook_app):
    monkeypatch.setattr("routers.webhooks.settings.profile_impression_webhook_secret", "configured-secret")

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/webhooks/profile-impression",
            json={"user_id": "missing_user_id", "count": 1},
            headers={"X-Webhook-Secret": "configured-secret"},
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_profile_impression_webhook_disabled_without_env(monkeypatch, webhook_app):
    monkeypatch.setattr("routers.webhooks.settings.profile_impression_webhook_secret", None)

    transport = ASGITransport(app=webhook_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/webhooks/profile-impression",
            json={"user_id": "x", "count": 1},
            headers={"X-Webhook-Secret": "anything"},
        )
    assert r.status_code == 503
