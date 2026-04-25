"""MonitorAgent summarizes pipeline rows when orchestration passes application context (TASK-022)."""

import pytest

from agents.monitor import MonitorAgent


@pytest.mark.asyncio
async def test_monitor_empty_context() -> None:
    out = await MonitorAgent().run({})
    assert out == {"changes": []}


@pytest.mark.asyncio
async def test_monitor_flags_stale_application_rows() -> None:
    out = await MonitorAgent().run(
        {
            "applications": [
                {"id": "app-1", "is_stale": True, "status": "pending"},
                {"id": "app-2", "is_stale": False},
                "skip-me",
            ]
        }
    )
    changes = out["changes"]
    assert len(changes) == 1
    assert changes[0]["application_id"] == "app-1"
    assert changes[0]["type"] == "stale_pipeline_row"


@pytest.mark.asyncio
async def test_monitor_dedup_group_surfaces() -> None:
    out = await MonitorAgent().run(
        {
            "applications": [
                {"id": "a", "is_stale": False, "dedup_group": "g1"},
            ]
        }
    )
    changes = out["changes"]
    assert len(changes) == 1
    assert changes[0]["type"] == "dedup_group"
    assert changes[0]["dedup_group"] == "g1"
