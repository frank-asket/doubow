"""LangGraph control-flow tests for autopilot parity graph."""

import pytest

from workflow.autopilot_langgraph import AutopilotGraphState, run_autopilot_via_langgraph


@pytest.mark.asyncio
async def test_langgraph_runs_explicit_nodes_in_order():
    calls: list[str] = []

    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("mark_running")
        return {"halt": False}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("resolve_targets")
        return {"app_ids": ["a1"]}

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("process_items")
        return {"item_payload": []}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_done")
        return {"ok": True}

    async def _persist_failed(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_failed")
        return {"ok": False}

    await run_autopilot_via_langgraph(
        initial_state={},
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
    )

    assert calls == [
        "mark_running",
        "resolve_targets",
        "process_items",
        "persist_done",
    ]


@pytest.mark.asyncio
async def test_langgraph_halts_when_mark_running_returns_false():
    calls: list[str] = []

    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("mark_running")
        return {"halt": True}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("resolve_targets")
        return {}

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("process_items")
        return {}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_done")
        return {}

    async def _persist_failed(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_failed")
        return {}

    await run_autopilot_via_langgraph(
        initial_state={},
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
    )

    assert calls == ["mark_running"]


@pytest.mark.asyncio
async def test_langgraph_propagates_node_errors():
    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {"halt": False}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {"error_code": "resolve_failed", "error_detail": "resolve failed"}

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {}

    async def _persist_failed(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {"ok": False}

    out = await run_autopilot_via_langgraph(
        initial_state={},
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
    )
    assert out.get("error_code") == "resolve_failed"
    assert out.get("failed_node") == "resolve_targets"


@pytest.mark.asyncio
async def test_langgraph_emits_node_trace_events():
    events: list[dict[str, object]] = []

    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {"halt": False}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {}

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {"ok": True}

    async def _persist_failed(_state: AutopilotGraphState) -> AutopilotGraphState:
        return {"ok": False}

    await run_autopilot_via_langgraph(
        initial_state={},
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
        on_node_event=lambda event: events.append(dict(event)),
    )

    assert [(str(e["node"]), str(e["phase"])) for e in events] == [
        ("mark_running", "start"),
        ("mark_running", "end"),
        ("resolve_targets", "start"),
        ("resolve_targets", "end"),
        ("process_items", "start"),
        ("process_items", "end"),
        ("persist_done", "start"),
        ("persist_done", "end"),
    ]


@pytest.mark.asyncio
async def test_langgraph_routes_to_persist_failed_node():
    calls: list[str] = []

    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("mark_running")
        return {"halt": False}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("resolve_targets")
        return {"error_code": "resolve_failed", "error_detail": "bad query"}

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("process_items")
        return {}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_done")
        return {"ok": True}

    async def _persist_failed(state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_failed")
        return {
            "ok": False,
            "error_code": str(state.get("error_code") or ""),
            "failed_node": str(state.get("failed_node") or ""),
        }

    out = await run_autopilot_via_langgraph(
        initial_state={},
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
    )
    assert calls == ["mark_running", "resolve_targets", "persist_failed"]
    assert out.get("ok") is False
    assert out.get("error_code") == "resolve_failed"
    assert out.get("failed_node") == "resolve_targets"


@pytest.mark.asyncio
async def test_langgraph_retries_retryable_resolve_targets_failure():
    calls: list[str] = []
    attempts = {"resolve_targets": 0}

    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("mark_running")
        return {"halt": False}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("resolve_targets")
        attempts["resolve_targets"] += 1
        if attempts["resolve_targets"] == 1:
            return {
                "error_code": "resolve_failed",
                "error_detail": "temporary db timeout",
                "retryable_error": True,
            }
        return {"app_ids": ["a1"]}

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("process_items")
        return {"item_payload": []}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_done")
        return {"ok": True}

    async def _persist_failed(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_failed")
        return {"ok": False}

    out = await run_autopilot_via_langgraph(
        initial_state={"retry_count": 0, "max_retries": 1},
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
    )

    assert calls == [
        "mark_running",
        "resolve_targets",
        "resolve_targets",
        "process_items",
        "persist_done",
    ]
    assert out.get("ok") is True
    assert out.get("retry_count") == 1


@pytest.mark.asyncio
async def test_langgraph_stops_after_retry_budget_exhausted():
    calls: list[str] = []

    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("mark_running")
        return {"halt": False}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("resolve_targets")
        return {
            "error_code": "resolve_failed",
            "error_detail": "still failing",
            "retryable_error": True,
        }

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("process_items")
        return {}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_done")
        return {}

    async def _persist_failed(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_failed")
        return {"ok": False}

    out = await run_autopilot_via_langgraph(
        initial_state={"retry_count": 0, "max_retries": 1},
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
    )

    assert calls == ["mark_running", "resolve_targets", "resolve_targets", "persist_failed"]
    assert out.get("ok") is False
    assert out.get("error_code") == "resolve_failed"


@pytest.mark.asyncio
async def test_langgraph_resume_entry_skips_completed_nodes():
    calls: list[str] = []

    async def _mark_running(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("mark_running")
        return {"halt": False, "scope": "all"}

    async def _resolve_targets(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("resolve_targets")
        return {"app_ids": ["a1"]}

    async def _process_items(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("process_items")
        return {"item_payload": []}

    async def _persist_done(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_done")
        return {"ok": True}

    async def _persist_failed(_state: AutopilotGraphState) -> AutopilotGraphState:
        calls.append("persist_failed")
        return {"ok": False}

    await run_autopilot_via_langgraph(
        initial_state={
            "run_id": "r1",
            "user_id": "u1",
            "resume_entry_node": "process_items",
            "scope": "all",
            "app_ids": ["a1"],
        },
        mark_running=_mark_running,
        resolve_targets=_resolve_targets,
        process_items=_process_items,
        persist_done=_persist_done,
        persist_failed=_persist_failed,
    )

    assert calls == ["process_items", "persist_done"]
