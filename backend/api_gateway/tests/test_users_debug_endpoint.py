from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from config import settings
from models.user import User
from routers import users


@pytest.mark.asyncio
async def test_email_identity_debug_shows_multiple_ids_for_same_email(db_session: AsyncSession):
    email = "same@example.com"
    now = datetime.now(timezone.utc)
    first = User(id="user_a", email=email, created_at=now - timedelta(days=2))
    second = User(id="user_b", email="Same@example.com", created_at=now - timedelta(days=1))
    db_session.add(first)
    db_session.add(second)
    await db_session.commit()

    app = FastAPI()
    app.include_router(users.router, prefix="/v1")

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return second

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_user

    with TestClient(app) as client:
        res = client.get("/v1/me/debug/email-identities")
    assert res.status_code == 200
    payload = res.json()
    assert payload["email"] == "Same@example.com"
    assert payload["current_user_id"] == "user_b"
    assert payload["multiple_ids_for_same_email"] is True
    assert [row["user_id"] for row in payload["ids_for_email"]] == ["user_a", "user_b"]


@pytest.mark.asyncio
async def test_ai_config_debug_endpoint_returns_safe_model_resolution(db_session: AsyncSession, monkeypatch):
    user = User(id="user_ai_cfg", email="ai@example.com")
    db_session.add(user)
    await db_session.commit()

    monkeypatch.setattr(settings, "openrouter_api_key", "secret_should_not_leak")
    monkeypatch.setattr(settings, "openrouter_api_url", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "openrouter_model", "anthropic/claude-sonnet-4.6")
    monkeypatch.setattr(settings, "openrouter_model_chat", "openai/gpt-4.1-mini")
    monkeypatch.setattr(settings, "openrouter_model_drafts", None)
    monkeypatch.setattr(settings, "openrouter_model_prep", None)
    monkeypatch.setattr(settings, "openrouter_model_resume", None)

    app = FastAPI()
    app.include_router(users.router, prefix="/v1")

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return user

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_user

    with TestClient(app) as client:
        res = client.get("/v1/me/debug/ai-config")
    assert res.status_code == 200
    payload = res.json()
    assert payload["openrouter_configured"] is True
    assert payload["openrouter_api_url"] == "https://openrouter.ai/api/v1"
    assert payload["resolved_models"]["chat"] == "openai/gpt-4.1-mini"
    assert payload["resolved_models"]["drafts"] == "anthropic/claude-sonnet-4.6"
    assert "openrouter_api_key" not in payload
    assert "secret_should_not_leak" not in str(payload)


@pytest.mark.asyncio
async def test_oauth_config_debug_endpoint_reports_missing_keys(db_session: AsyncSession, monkeypatch):
    user = User(id="user_oauth_cfg", email="oauth@example.com")
    db_session.add(user)
    await db_session.commit()

    monkeypatch.setattr(settings, "google_oauth_client_id", "gid")
    monkeypatch.setattr(settings, "google_oauth_client_secret", None)
    monkeypatch.setattr(settings, "google_oauth_redirect_uri", "https://api.example.com/v1/integrations/google/callback")
    monkeypatch.setattr(settings, "google_oauth_state_secret", "gstate")
    monkeypatch.setattr(settings, "google_oauth_token_fernet_key", None)

    monkeypatch.setattr(settings, "linkedin_oauth_client_id", "lid")
    monkeypatch.setattr(settings, "linkedin_oauth_client_secret", None)
    monkeypatch.setattr(settings, "linkedin_oauth_redirect_uri", "https://api.example.com/v1/integrations/linkedin/callback")
    monkeypatch.setattr(settings, "linkedin_oauth_state_secret", "lstate")

    app = FastAPI()
    app.include_router(users.router, prefix="/v1")

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return user

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_user

    with TestClient(app) as client:
        res = client.get("/v1/me/debug/oauth-config")
    assert res.status_code == 200
    payload = res.json()
    assert payload["google"]["configured"] is False
    assert "GOOGLE_OAUTH_CLIENT_SECRET" in payload["google"]["missing_required_keys"]
    assert "GOOGLE_OAUTH_TOKEN_FERNET_KEY" in payload["google"]["missing_required_keys"]
    assert payload["linkedin"]["configured"] is False
    assert "LINKEDIN_OAUTH_CLIENT_SECRET" in payload["linkedin"]["missing_required_keys"]
    assert "LINKEDIN_OAUTH_TOKEN_FERNET_KEY_OR_GOOGLE_FALLBACK" in payload["linkedin"]["missing_required_keys"]


@pytest.mark.asyncio
async def test_feedback_learning_prefs_require_resume(db_session: AsyncSession, monkeypatch):
    """Without a résumé row, read/clear return 404 in all environments (including production)."""
    monkeypatch.setattr(settings, "environment", "production")
    user = User(id="user_fl_prod", email="fl-prod@example.com")
    db_session.add(user)
    await db_session.commit()

    app = FastAPI()
    app.include_router(users.router, prefix="/v1")

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return user

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_user

    with TestClient(app) as client:
        res_get = client.get("/v1/me/preferences/feedback-learning")
        res_del = client.delete("/v1/me/preferences/feedback-learning")
    assert res_get.status_code == 404
    assert "resume" in res_get.json()["detail"].lower()
    assert res_del.status_code == 404
    assert "resume" in res_del.json()["detail"].lower()
