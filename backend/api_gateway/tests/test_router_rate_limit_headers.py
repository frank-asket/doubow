from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from routers import autopilot as autopilot_router
from routers import ingestion as ingestion_router
from services.rate_limit_service import RateLimitBackendUnavailableError
from services.rate_limit_service import RateLimitExceededError


class _DummySession:
    async def execute(self, *args, **kwargs):  # pragma: no cover - test stub
        raise RuntimeError("session should not be used when limiter blocks")

    async def commit(self):  # pragma: no cover - test stub
        return None


async def _override_session() -> AsyncGenerator[_DummySession, None]:
    yield _DummySession()


async def _override_authenticated_user() -> User:
    return User(id="user_test_123", email="test@example.com", name="Test User", plan="free")


def _build_test_client(*, include_autopilot: bool = False, include_ingestion: bool = False) -> TestClient:
    app = FastAPI()
    if include_autopilot:
        app.include_router(autopilot_router.router, prefix="/v1")
    if include_ingestion:
        app.include_router(ingestion_router.router, prefix="/v1")
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_authenticated_user
    return TestClient(app)


@pytest.mark.parametrize(
    ("path", "payload", "headers"),
    [
        ("/v1/me/autopilot/run", {"scope": "all", "application_ids": ["app_1"]}, {"Idempotency-Key": "idem_12345678"}),
        ("/v1/me/autopilot/runs/run_123/resume", None, {}),
    ],
)
def test_autopilot_routes_return_429_with_retry_after_when_limited(monkeypatch, path, payload, headers):
    async def _raise_limited(**_kwargs):
        raise RateLimitExceededError(bucket="autopilot_test", retry_after_s=7)

    monkeypatch.setattr(autopilot_router, "enforce_user_window_limit", _raise_limited)

    with _build_test_client(include_autopilot=True) as client:
        if payload is None:
            response = client.post(path, headers=headers)
        else:
            response = client.post(path, json=payload, headers=headers)

    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "7"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/v1/admin/ingestion/run"),
        ("get", "/v1/admin/ingestion/health"),
    ],
)
def test_ingestion_routes_return_429_with_retry_after_when_limited(monkeypatch, method, path):
    async def _raise_limited(**_kwargs):
        raise RateLimitExceededError(bucket="ingestion_test", retry_after_s=9)

    monkeypatch.setattr(ingestion_router, "enforce_user_window_limit", _raise_limited)

    with _build_test_client(include_ingestion=True) as client:
        response = getattr(client, method)(path)

    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "9"


@pytest.mark.parametrize(
    ("path", "payload", "headers"),
    [
        ("/v1/me/autopilot/run", {"scope": "all", "application_ids": ["app_1"]}, {"Idempotency-Key": "idem_12345678"}),
        ("/v1/me/autopilot/runs/run_123/resume", None, {}),
    ],
)
def test_autopilot_routes_return_503_when_rate_limit_backend_unavailable(monkeypatch, path, payload, headers):
    async def _raise_unavailable(**_kwargs):
        raise RateLimitBackendUnavailableError("backend unavailable")

    monkeypatch.setattr(autopilot_router, "enforce_user_window_limit", _raise_unavailable)

    with _build_test_client(include_autopilot=True) as client:
        if payload is None:
            response = client.post(path, headers=headers)
        else:
            response = client.post(path, json=payload, headers=headers)

    assert response.status_code == 503
    assert response.headers.get("Retry-After") is None


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/v1/admin/ingestion/run"),
        ("get", "/v1/admin/ingestion/health"),
    ],
)
def test_ingestion_routes_return_503_when_rate_limit_backend_unavailable(monkeypatch, method, path):
    async def _raise_unavailable(**_kwargs):
        raise RateLimitBackendUnavailableError("backend unavailable")

    monkeypatch.setattr(ingestion_router, "enforce_user_window_limit", _raise_unavailable)

    with _build_test_client(include_ingestion=True) as client:
        response = getattr(client, method)(path)

    assert response.status_code == 503
    assert response.headers.get("Retry-After") is None
