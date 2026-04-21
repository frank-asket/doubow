"""Typed JSON error envelope for HTTPException and validation errors."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
import sys
import types
import fastapi.dependencies.utils as fastapi_dep_utils

from error_handlers import register_exception_handlers
from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User


def test_http_exception_returns_error_envelope():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/gone")
    async def gone():
        raise HTTPException(status_code=404, detail="Resource not found")

    client = TestClient(app)
    res = client.get("/gone")
    assert res.status_code == 404
    body = res.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Resource not found"


def test_validation_error_returns_error_envelope():
    app = FastAPI()
    register_exception_handlers(app)

    class Payload(BaseModel):
        name: str

    @app.post("/echo")
    async def echo(_: Payload):
        return {"ok": True}

    client = TestClient(app)
    res = client.post("/echo", json={})
    assert res.status_code == 422
    body = res.json()
    assert body["error"]["code"] == "validation_error"
    assert "message" in body["error"]
    assert body["error"]["details"] is not None


@pytest.mark.asyncio
async def test_main_app_mutating_route_404_uses_global_error_envelope(monkeypatch):
    # Keep test isolated from optional resume parser deps when importing main app.
    fake_docx = types.ModuleType("docx")
    fake_docx.Document = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "docx", fake_docx)
    fake_pypdf = types.ModuleType("pypdf")
    fake_pypdf.PdfReader = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pypdf", fake_pypdf)
    monkeypatch.setattr(fastapi_dep_utils, "ensure_multipart_is_installed", lambda: None)

    from main import app as main_app

    async def _override_user() -> User:
        return User(id="u_test_err", email="u_test_err@example.com", name="T", plan="free")

    async def _override_session():
        fake = AsyncMock(spec=AsyncSession)
        fake.execute = AsyncMock()
        yield fake

    async def _raise_not_found(**kwargs):
        raise LookupError("job_not_found")

    monkeypatch.setattr("routers.jobs.dismiss_job_for_user", _raise_not_found)
    main_app.dependency_overrides[get_authenticated_user] = _override_user
    main_app.dependency_overrides[get_session] = _override_session
    try:
        client = TestClient(main_app)
        res = client.post("/v1/jobs/job_missing/dismiss")
        assert res.status_code == 404
        body = res.json()
        assert body["error"]["code"] == "not_found"
        assert body["error"]["message"] == "Job not found"
    finally:
        main_app.dependency_overrides.pop(get_authenticated_user, None)
        main_app.dependency_overrides.pop(get_session, None)
