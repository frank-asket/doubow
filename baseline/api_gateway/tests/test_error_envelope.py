"""Typed JSON error envelope for HTTPException and validation errors."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from error_handlers import register_exception_handlers


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
