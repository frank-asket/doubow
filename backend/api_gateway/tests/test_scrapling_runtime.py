"""Scrapling runtime path (seed URLs + mocked HTTP)."""

import pytest

from config import settings
from services.provider_adapter import ProviderFetchParams
from services.scrapling_adapter import ScraplingAdapter, _invoke_scrapling_runtime

LD_PAGE = """
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"JobPosting","title":"SRE","url":"https://jobs.example.com/1",
"hiringOrganization":{"@type":"Organization","name":"Acme"},
"jobLocation":{"@type":"Place","name":"Remote"}}
</script>
"""


def test_invoke_runtime_returns_jobs_when_http_mocked(monkeypatch):
    monkeypatch.setattr(settings, "scrapling_seed_urls", "https://jobs.example.com/page")
    monkeypatch.setattr(settings, "scrapling_timeout_s", 30.0)

    def fake_get(url: str, _timeout: float) -> str:
        assert "jobs.example.com" in url
        return LD_PAGE

    monkeypatch.setattr("services.scrapling_adapter._http_get_text", fake_get)

    rows = _invoke_scrapling_runtime(
        ProviderFetchParams(keywords=None, location=None, page=1, per_page=10),
        settings,
    )
    assert len(rows) == 1
    assert rows[0]["title"] == "SRE"
    assert rows[0]["company"] == "Acme"


@pytest.mark.asyncio
async def test_fetch_jobs_runtime_mode(monkeypatch):
    monkeypatch.setattr(settings, "scrapling_enabled", True)
    monkeypatch.setattr(settings, "scrapling_fixture_json_path", None)
    monkeypatch.setattr(settings, "scrapling_bundle_fixture", False)
    monkeypatch.setattr(settings, "scrapling_seed_urls", "https://jobs.example.com/p")
    monkeypatch.setattr(settings, "scrapling_timeout_s", 30.0)

    monkeypatch.setattr("services.scrapling_adapter._http_get_text", lambda url, t: LD_PAGE)

    adapter = ScraplingAdapter(settings)
    res = await adapter.fetch_jobs(ProviderFetchParams(keywords=None, page=1, per_page=10))
    assert res.metadata.get("mode") == "runtime"
    assert len(res.jobs) == 1
    assert res.jobs[0].title == "SRE"
