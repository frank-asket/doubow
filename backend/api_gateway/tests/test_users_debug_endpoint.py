from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
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
