import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_session
from dependencies import get_authenticated_user
from error_handlers import register_exception_handlers
from models.user import User
from routers import resume


@pytest_asyncio.fixture
async def resume_test_app(db_session: AsyncSession) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(resume.router, prefix="/v1")

    async def _override_session():
        yield db_session

    async def _override_user() -> User:
        return User(id="u_resume_lc", email="u_resume_lc@example.com", name="Resume LC", plan="free")

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_user

    db_session.add(User(id="u_resume_lc", email="u_resume_lc@example.com"))
    await db_session.commit()
    return app


@pytest.mark.asyncio
async def test_resume_analyze_uses_langchain_when_enabled(tmp_path, monkeypatch, resume_test_app: FastAPI):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "use_langchain", True)
    monkeypatch.setattr(settings, "openrouter_api_key", "or_test_key")

    called = {"value": False}

    async def _langchain(parsed, prefs):
        called["value"] = True
        return "Summary: LangChain integration path"

    monkeypatch.setattr("services.resume_service.analyze_resume_with_langchain", _langchain)

    async with AsyncClient(transport=ASGITransport(app=resume_test_app), base_url="http://test") as client:
        upload = await client.post(
            "/v1/me/resume",
            files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert upload.status_code == 200, upload.text

        analyzed = await client.post("/v1/me/resume/analyze")
        assert analyzed.status_code == 200, analyzed.text
        assert analyzed.json()["analysis"] == "Summary: LangChain integration path"
        assert called["value"] is True


@pytest.mark.asyncio
async def test_resume_analyze_langchain_failure_falls_back(tmp_path, monkeypatch, resume_test_app: FastAPI):
    monkeypatch.setattr(settings, "resume_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "use_langchain", True)
    monkeypatch.setattr(settings, "openrouter_api_key", "or_test_key")

    async def _boom(*args, **kwargs):
        raise RuntimeError("langchain down")

    monkeypatch.setattr("services.resume_service.analyze_resume_with_langchain", _boom)
    monkeypatch.setattr("services.resume_service.build_profile_analysis", lambda parsed, prefs: "Fallback analysis")

    async with AsyncClient(transport=ASGITransport(app=resume_test_app), base_url="http://test") as client:
        upload = await client.post(
            "/v1/me/resume",
            files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert upload.status_code == 200, upload.text

        analyzed = await client.post("/v1/me/resume/analyze")
        assert analyzed.status_code == 200, analyzed.text
        assert analyzed.json()["analysis"] == "Fallback analysis"
