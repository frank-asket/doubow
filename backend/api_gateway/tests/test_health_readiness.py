"""Liveness / readiness endpoints and dependency probes."""

import sys
import types

import pytest
from fastapi.testclient import TestClient
import fastapi.dependencies.utils as fastapi_dep_utils


@pytest.fixture
def main_app(monkeypatch):
    """Import ``main.app`` without optional resume parser deps."""
    fake_docx = types.ModuleType("docx")
    fake_docx.Document = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "docx", fake_docx)
    fake_pypdf = types.ModuleType("pypdf")
    fake_pypdf.PdfReader = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pypdf", fake_pypdf)
    monkeypatch.setattr(fastapi_dep_utils, "ensure_multipart_is_installed", lambda: None)

    from main import app

    # Lifespan calls init_models(), which needs Postgres; these tests only exercise HTTP routes.
    async def _skip_db_init() -> None:
        return None

    monkeypatch.setattr("main.init_models", _skip_db_init)

    return app


def test_healthz_ok(main_app):
    with TestClient(main_app) as client:
        res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ready_postgres_failure_returns_503(main_app, monkeypatch):
    import services.health_checks as hc

    async def fail_pg() -> tuple[bool, str | None]:
        return False, "connection refused"

    async def ok_redis() -> tuple[bool, str | None]:
        return True, None

    monkeypatch.setattr(hc, "check_postgres", fail_pg)
    monkeypatch.setattr(hc, "check_redis", ok_redis)

    with TestClient(main_app) as client:
        res = client.get("/ready")
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "not_ready"
    assert body["postgres"] == "error"
    assert body["redis"] == "ok"


def test_ready_redis_degraded_still_200(main_app, monkeypatch):
    import services.health_checks as hc

    async def ok_pg() -> tuple[bool, str | None]:
        return True, None

    async def bad_redis() -> tuple[bool, str | None]:
        return False, "redis down"

    monkeypatch.setattr(hc, "check_postgres", ok_pg)
    monkeypatch.setattr(hc, "check_redis", bad_redis)

    with TestClient(main_app) as client:
        res = client.get("/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ready"
    assert body["postgres"] == "ok"
    assert body["redis"] == "degraded"
    assert body.get("redis_detail") == "redis down"


def test_ready_includes_background_durability(main_app, monkeypatch):
    import services.health_checks as hc

    async def ok_pg() -> tuple[bool, str | None]:
        return True, None

    async def ok_redis() -> tuple[bool, str | None]:
        return True, None

    async def ok_celery() -> tuple[bool, str | None]:
        return True, None

    monkeypatch.setattr(hc, "check_postgres", ok_pg)
    monkeypatch.setattr(hc, "check_redis", ok_redis)
    monkeypatch.setattr(hc, "check_celery_enqueue_health", ok_celery)

    with TestClient(main_app) as client:
        res = client.get("/ready")
    assert res.status_code == 200
    body = res.json()
    assert "background_durability" in body
    bg = body["background_durability"]
    assert bg["send_mode"] in {"celery", "inprocess"}
    assert bg["autopilot_mode"] in {"celery", "inprocess"}
    assert bg["enqueue"] in {"ok", "error"}
