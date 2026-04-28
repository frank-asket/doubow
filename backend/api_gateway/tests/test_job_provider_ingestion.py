import pytest
from sqlalchemy import select
from fastapi.testclient import TestClient

from config import settings
from models.job import Job
from models.job_ingestion_run import JobIngestionRun
from models.job_source_record import JobSourceRecord
from models.user import User
from db.session import get_session
from dependencies import get_authenticated_user
from routers.jobs import router as jobs_router
from schemas.jobs import DiscoverJobItem
from services.adzuna_adapter import resolve_adzuna_scheduled_ingest_params
from services.job_provider_ingestion_service import ingest_provider_jobs_paginated
from services.provider_adapter import ProviderAdapter, ProviderFetchParams, ProviderFetchResult


class _FakeProvider(ProviderAdapter):
    provider_name = "fake_provider"

    async def fetch_jobs(self, params: ProviderFetchParams) -> ProviderFetchResult:
        job = DiscoverJobItem(
            source="manual",
            external_id=f"fake-{params.page}",
            title="Backend Engineer",
            company="Example Co",
            location="Remote",
            description="Build APIs",
            url=f"https://example.com/jobs/{params.page}",
        )
        return ProviderFetchResult(
            provider=self.provider_name,
            jobs=[job],
            raw_records=[(f"fake-{params.page}", {"id": f"fake-{params.page}", "title": "Backend Engineer"})],
            metadata={"page": params.page},
        )


@pytest.mark.asyncio
async def test_ingest_provider_jobs_paginated_creates_runs_sources_and_jobs(db_session):
    user_id = "ingest_user_1"
    db_session.add(User(id=user_id, email="ingest@example.com"))
    await db_session.commit()

    summary = await ingest_provider_jobs_paginated(
        db_session,
        user_id=user_id,
        adapter=_FakeProvider(),
        base_params=ProviderFetchParams(page=1, per_page=10),
        pages=2,
    )

    assert summary["provider"] == "fake_provider"
    assert summary["pages"] == 2
    assert summary["created"] == 1
    assert summary["updated"] == 0
    assert summary["deduped"] >= 1
    assert len(summary["run_ids"]) == 2

    runs = (await db_session.execute(select(JobIngestionRun))).scalars().all()
    assert len(runs) == 2
    assert all(r.status == "completed" for r in runs)

    source_records = (await db_session.execute(select(JobSourceRecord))).scalars().all()
    assert len(source_records) == 2

    jobs = (await db_session.execute(select(Job).where(Job.company == "Example Co"))).scalars().all()
    assert len(jobs) == 1


@pytest.mark.asyncio
async def test_ingest_provider_jobs_paginated_dedupes_against_existing_catalog(db_session):
    user_id = "ingest_user_2"
    db_session.add(User(id=user_id, email="ingest2@example.com"))
    db_session.add(
        Job(
            id="jb_existing_1",
            source="catalog",
            external_id="existing-1",
            title="Backend Engineer",
            company="Example Co",
            location="Remote",
            salary_range=None,
            description="Build APIs",
            url="https://example.com/existing",
            score_template=None,
        )
    )
    await db_session.commit()

    summary = await ingest_provider_jobs_paginated(
        db_session,
        user_id=user_id,
        adapter=_FakeProvider(),
        base_params=ProviderFetchParams(page=1, per_page=10),
        pages=1,
    )

    assert summary["created"] == 0
    assert summary["updated"] == 0
    assert summary["deduped"] >= 1


def test_resolve_adzuna_scheduled_ingest_params(monkeypatch):
    monkeypatch.setattr(settings, "adzuna_ingest_hourly_pages", 2)
    monkeypatch.setattr(settings, "adzuna_ingest_daily_pages", 7)
    monkeypatch.setattr(settings, "adzuna_country", "de")
    monkeypatch.setattr(settings, "adzuna_results_per_page", 50)
    monkeypatch.setattr(settings, "adzuna_ingest_default_keywords", "engineer")
    monkeypatch.setattr(settings, "adzuna_ingest_default_location", None)

    pages_h, p_h = resolve_adzuna_scheduled_ingest_params(settings, preset="hourly")
    assert pages_h == 2
    assert p_h.keywords == "engineer"
    assert p_h.country == "de"

    pages_d, p_d = resolve_adzuna_scheduled_ingest_params(
        settings,
        preset="daily",
        keywords="pm",
        location="Berlin",
        country="",
        start_page=2,
    )
    assert pages_d == 7
    assert p_d.keywords == "pm"
    assert p_d.location == "Berlin"
    assert p_d.page == 2


def test_catalog_ingest_preset_returns_partial_when_one_provider_fails(monkeypatch):
    from routers import jobs as jobs_router_module

    monkeypatch.setattr(settings, "job_catalog_ingestion_user_id", "catalog_ingestion_system")
    monkeypatch.setattr(settings, "greenhouse_board_tokens", "openai,notion")

    async def _fake_ingest_provider_jobs_paginated(session, *, user_id, adapter, base_params, pages):  # type: ignore[no-untyped-def]
        if adapter.provider_name == "adzuna":
            return {
                "provider": "adzuna",
                "pages": pages,
                "created": 2,
                "updated": 1,
                "job_ids": ["j1", "j2", "j3"],
                "run_ids": ["r1"],
                "deduped": 0,
            }
        raise RuntimeError("greenhouse upstream timeout")

    monkeypatch.setattr(jobs_router_module, "ingest_provider_jobs_paginated", _fake_ingest_provider_jobs_paginated)

    # Build a minimal FastAPI app to serve the router with auth/session overrides.
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(jobs_router, prefix="/v1")

    async def _override_session():  # type: ignore[no-untyped-def]
        yield object()

    async def _override_authenticated_user() -> User:
        return User(id="user_test_123", email="test@example.com", name="Test User", plan="free")

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_authenticated_user
    client = TestClient(app)
    res = client.post("/v1/jobs/providers/catalog/ingest/preset?preset=hourly")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "partial"
    assert body["created"] == 2
    assert body["updated"] == 1
    assert len(body["providers"]) == 2
    by_provider = {p["provider"]: p for p in body["providers"]}
    assert by_provider["adzuna"]["status"] == "completed"
    assert by_provider["greenhouse"]["status"] == "failed"


def test_catalog_ingest_preset_returns_failed_when_all_providers_fail(monkeypatch):
    from routers import jobs as jobs_router_module

    monkeypatch.setattr(settings, "job_catalog_ingestion_user_id", "catalog_ingestion_system")
    monkeypatch.setattr(settings, "greenhouse_board_tokens", "openai,notion")

    async def _all_fail_ingest_provider_jobs_paginated(session, *, user_id, adapter, base_params, pages):  # type: ignore[no-untyped-def]
        raise RuntimeError(f"{adapter.provider_name} unavailable")

    monkeypatch.setattr(jobs_router_module, "ingest_provider_jobs_paginated", _all_fail_ingest_provider_jobs_paginated)

    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(jobs_router, prefix="/v1")

    async def _override_session():  # type: ignore[no-untyped-def]
        yield object()

    async def _override_authenticated_user() -> User:
        return User(id="user_test_123", email="test@example.com", name="Test User", plan="free")

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_authenticated_user

    client = TestClient(app)
    res = client.post("/v1/jobs/providers/catalog/ingest/preset?preset=hourly")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "failed"
    assert body["created"] == 0
    assert body["updated"] == 0
    assert body["run_ids"] == []
    assert body["job_ids"] == []
    assert len(body["providers"]) == 2
    by_provider = {p["provider"]: p for p in body["providers"]}
    assert by_provider["adzuna"]["status"] == "failed"
    assert by_provider["greenhouse"]["status"] == "failed"
