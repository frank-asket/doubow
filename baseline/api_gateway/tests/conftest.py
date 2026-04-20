from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from db.session import get_session
from db.session import Base
from dependencies import get_authenticated_user
from models.user import User
import models  # noqa: F401
from routers import applications, approvals, autopilot


class _DummySession:
    async def execute(self, *args, **kwargs):  # pragma: no cover - test stub
        raise RuntimeError("session should be mocked in tests")

    def add(self, *args, **kwargs):  # pragma: no cover - test stub
        return None

    async def commit(self):  # pragma: no cover - test stub
        return None


async def _override_session() -> AsyncGenerator[_DummySession, None]:
    yield _DummySession()


async def _override_authenticated_user() -> User:
    return User(id="user_test_123", email="test@example.com", name="Test User", plan="free")


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(applications.router, prefix="/v1")
    app.include_router(autopilot.router, prefix="/v1")
    app.include_router(approvals.router, prefix="/v1")
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_authenticated_user
    return TestClient(app)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()
