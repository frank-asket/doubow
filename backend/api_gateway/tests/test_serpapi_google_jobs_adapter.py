"""SerpAPI Google Jobs adapter (mocked HTTP)."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from config import settings
from services.provider_adapter import ProviderFetchParams
from services.serpapi_google_jobs_adapter import SerpApiGoogleJobsAdapter


@pytest.mark.asyncio
async def test_fetch_jobs_maps_serpapi_payload(monkeypatch):
    monkeypatch.setattr(settings, "serpapi_api_key", "test-key")
    monkeypatch.setattr(settings, "google_jobs_serp_max_rounds", 1)

    payload = {
        "jobs_results": [
            {
                "title": "Backend Engineer",
                "company_name": "Acme",
                "location": "Remote",
                "description": "Build APIs.",
                "job_id": "jid123",
                "share_link": "https://www.google.com/search?udm=8&q=test",
                "thumbnail": "https://example.com/logo.png",
                "apply_options": [{"title": "Lever", "link": "https://jobs.lever.co/acme/123"}],
            }
        ],
        "serpapi_pagination": {},
    }

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    async def _fake_get(url, params=None):  # type: ignore[no-untyped-def]
        r = MagicMock()
        r.raise_for_status = lambda: None
        r.json = lambda: payload
        return r

    mock_client.get = AsyncMock(side_effect=_fake_get)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: mock_client)

    adapter = SerpApiGoogleJobsAdapter()
    res = await adapter.fetch_jobs(
        ProviderFetchParams(keywords="python django", location="Austin, TX", page=1, per_page=10)
    )
    assert res.provider == "google_jobs"
    assert len(res.jobs) == 1
    assert res.jobs[0].title == "Backend Engineer"
    assert res.jobs[0].company == "Acme"
    assert res.jobs[0].source == "google_jobs"
    assert res.jobs[0].url.startswith("http")


@pytest.mark.asyncio
async def test_fetch_jobs_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "serpapi_api_key", None)
    adapter = SerpApiGoogleJobsAdapter()
    with pytest.raises(RuntimeError, match="SERPAPI"):
        await adapter.fetch_jobs(ProviderFetchParams(keywords="x", location=None, page=1, per_page=10))
