"""DiscoveryAgent returns a structured connector plan for orchestrator / observability (TASK-011)."""

import pytest

from agents.discovery import KNOWN_JOB_SOURCES, DiscoveryAgent


@pytest.mark.asyncio
async def test_discovery_default_connector_plan() -> None:
    out = await DiscoveryAgent().run({})
    assert out["jobs"] == []
    assert "hint" in out
    assert out["connector_plan"] == ["adzuna", "greenhouse", "google_jobs", "manual", "catalog"]


@pytest.mark.asyncio
async def test_discovery_respects_prefer_sources() -> None:
    out = await DiscoveryAgent().run({"prefer_sources": ["linkedin", "unknown", "ashby"]})
    assert out["connector_plan"] == ["linkedin", "ashby"]
    for name in out["connector_plan"]:
        assert name in KNOWN_JOB_SOURCES
