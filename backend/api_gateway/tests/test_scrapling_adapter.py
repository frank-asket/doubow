"""Scrapling adapter — mapping + fixture-backed fetch (no live Scrapling dependency)."""

import json
from pathlib import Path

import pytest

from config import settings
from services.provider_adapter import ProviderFetchParams
from services.scrapling_adapter import (
    ScraplingAdapter,
    map_scrapling_batch,
    map_scrapling_record_to_discover_item,
)


def test_map_scrapling_record_minimal():
    raw = {
        "title": "Data Engineer",
        "company": "Contoso",
        "url": "https://jobs.example.com/listing/42",
        "description": "Build pipelines.",
        "location": "Remote",
    }
    item = map_scrapling_record_to_discover_item(raw)
    assert item is not None
    assert item.source == "scrapling"
    assert item.title == "Data Engineer"
    assert item.company == "Contoso"
    assert item.url.startswith("https://")
    assert item.description == "Build pipelines."
    assert item.external_id.startswith("scrapling-")


def test_map_scrapling_record_rejects_missing_url():
    assert map_scrapling_record_to_discover_item({"title": "X", "company": "Y"}) is None


def test_map_scrapling_batch_skips_invalid():
    items = map_scrapling_batch(
        [
            {"title": "A", "company": "B", "url": "https://a.test/1"},
            {"title": "", "company": "B", "url": "https://a.test/2"},
        ]
    )
    assert len(items) == 1
    assert items[0].title == "A"


@pytest.mark.asyncio
async def test_fetch_jobs_disabled_returns_empty(monkeypatch):
    monkeypatch.setattr(settings, "scrapling_enabled", False)
    adapter = ScraplingAdapter(settings)
    res = await adapter.fetch_jobs(ProviderFetchParams(keywords="python", page=1, per_page=10))
    assert res.provider == "scrapling"
    assert res.jobs == []
    assert res.metadata.get("skipped") is True


@pytest.mark.asyncio
async def test_fetch_jobs_uses_bundled_fixture_when_no_path(monkeypatch):
    """Bundled api_gateway/fixtures/scrapling_sample_jobs.json loads when enabled."""
    monkeypatch.setattr(settings, "scrapling_enabled", True)
    monkeypatch.setattr(settings, "scrapling_fixture_json_path", None)
    monkeypatch.setattr(settings, "scrapling_bundle_fixture", True)

    adapter = ScraplingAdapter(settings)
    res = await adapter.fetch_jobs(ProviderFetchParams(keywords=None, page=1, per_page=10))
    assert res.metadata.get("mode") == "fixture"
    assert len(res.jobs) >= 1
    assert res.jobs[0].source == "scrapling"


@pytest.mark.asyncio
async def test_fetch_jobs_fixture(tmp_path: Path, monkeypatch):
    fixture = tmp_path / "jobs.json"
    payload = {
        "jobs": [
            {
                "title": "Backend Dev",
                "company_name": "Acme",
                "job_url": "https://careers.acme.com/j/1",
                "description": "APIs",
            }
        ]
    }
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(settings, "scrapling_enabled", True)
    monkeypatch.setattr(settings, "scrapling_fixture_json_path", str(fixture))

    adapter = ScraplingAdapter(settings)
    res = await adapter.fetch_jobs(ProviderFetchParams(keywords=None, page=1, per_page=10))
    assert len(res.jobs) == 1
    assert res.jobs[0].title == "Backend Dev"
    assert res.jobs[0].company == "Acme"
    assert res.metadata.get("mode") == "fixture"
    assert len(res.raw_records) == 1
