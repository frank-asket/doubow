"""LangGraph scaffold for autopilot execution (structure parity mode).

Approval interrupt (``USE_LANGGRAPH_AUTOPILOT_APPROVAL_INTERRUPT=true``) uses ``langgraph.types.interrupt`` after
draft generation and a durable SQLite checkpointer so ``Command(resume=...)`` can continue across worker restarts.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from config import settings

_SQLITE_CHECKPOINTER = None
_SQLITE_CHECKPOINTER_CONN = None


async def get_autopilot_langgraph_checkpointer():
    """Shared durable SqliteSaver for interrupt/resume."""
    global _SQLITE_CHECKPOINTER
    global _SQLITE_CHECKPOINTER_CONN
    if _SQLITE_CHECKPOINTER is None:
        import aiosqlite
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        raw = (settings.langgraph_autopilot_checkpoint_db_path or "").strip() or "./data/langgraph/autopilot_checkpoints.sqlite"
        db_path = Path(raw).expanduser()
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(str(db_path))
        saver = AsyncSqliteSaver(conn)
        await saver.setup()
        _SQLITE_CHECKPOINTER_CONN = conn
        _SQLITE_CHECKPOINTER = saver
    return _SQLITE_CHECKPOINTER


def reset_autopilot_langgraph_checkpointer_for_tests() -> None:
    """Reset durable LangGraph checkpointer singleton (test helper)."""
    global _SQLITE_CHECKPOINTER
    global _SQLITE_CHECKPOINTER_CONN
    _SQLITE_CHECKPOINTER = None
    _SQLITE_CHECKPOINTER_CONN = None


class AutopilotGraphState(TypedDict, total=False):
    run_id: str
    user_id: str
    application_ids: list[str] | None
    resume_entry_node: str
    scope: str
    app_ids: list[str]
    item_payload: list[dict]
    ok: bool
    error_code: str
    error_detail: str
    failed_node: str
    retryable_error: bool
    retry_count: int
    max_retries: int
    retry_target_node: str
    halt: bool
    approval_resume: dict[str, Any]


class AutopilotGraphTraceEvent(TypedDict):
    node: str
    phase: Literal["start", "end", "error"]
    state: dict[str, Any]


def _snapshot_state(state: AutopilotGraphState) -> dict[str, Any]:
    return dict(state)


def _emit_trace(
    on_node_event: Callable[[AutopilotGraphTraceEvent], None] | None,
    *,
    node: str,
    phase: Literal["start", "end", "error"],
    state: AutopilotGraphState,
) -> None:
    if on_node_event is None:
        return
    on_node_event(
        AutopilotGraphTraceEvent(
            node=node,
            phase=phase,
            state=_snapshot_state(state),
        )
    )


def _build_autopilot_parity_graph(
    mark_running: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    resolve_targets: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    process_items: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    persist_done: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    persist_failed: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    on_node_event: Callable[[AutopilotGraphTraceEvent], None] | None = None,
    on_node_checkpoint: Callable[[str, AutopilotGraphState], Awaitable[None]] | None = None,
    *,
    approval_interrupt_enabled: bool = False,
    checkpointer: Any | None = None,
):
    """Create parity graph with explicit autopilot lifecycle nodes and retry/recovery routing."""

    def _can_retry(state: AutopilotGraphState) -> bool:
        if not state.get("retryable_error"):
            return False
        retries = int(state.get("retry_count") or 0)
        max_retries = int(state.get("max_retries") or 0)
        return retries < max_retries

    def _exception_error_state(node: str, detail: str, retryable: bool) -> AutopilotGraphState:
        return {
            "error_code": "node_exception",
            "error_detail": detail[:500],
            "failed_node": node,
            "retryable_error": retryable,
            "retry_target_node": node,
        }

    from langgraph.graph import END, START, StateGraph

    async def _maybe_checkpoint(node: str, state: AutopilotGraphState, out: AutopilotGraphState) -> None:
        if on_node_checkpoint is None or out.get("error_code"):
            return
        merged: AutopilotGraphState = {**dict(state), **out}
        await on_node_checkpoint(node, merged)

    async def _mark_running_node(state: AutopilotGraphState) -> AutopilotGraphState:
        _emit_trace(on_node_event, node="mark_running", phase="start", state=state)
        try:
            out = await mark_running(state)
            if out.get("error_code"):
                out = {**out, "failed_node": "mark_running", "retry_target_node": "mark_running"}
                _emit_trace(on_node_event, node="mark_running", phase="error", state={**state, **out})
                return out
            _emit_trace(on_node_event, node="mark_running", phase="end", state={**state, **out})
            await _maybe_checkpoint("mark_running", state, out)
            return out
        except Exception as exc:
            out = _exception_error_state("mark_running", str(exc), retryable=False)
            _emit_trace(on_node_event, node="mark_running", phase="error", state={**state, **out})
            return out

    async def _resolve_targets_node(state: AutopilotGraphState) -> AutopilotGraphState:
        _emit_trace(on_node_event, node="resolve_targets", phase="start", state=state)
        try:
            out = await resolve_targets(state)
            if out.get("error_code"):
                out = {**out, "failed_node": "resolve_targets", "retry_target_node": "resolve_targets"}
                _emit_trace(on_node_event, node="resolve_targets", phase="error", state={**state, **out})
                return out
            _emit_trace(on_node_event, node="resolve_targets", phase="end", state={**state, **out})
            await _maybe_checkpoint("resolve_targets", state, out)
            return out
        except Exception as exc:
            out = _exception_error_state("resolve_targets", str(exc), retryable=True)
            _emit_trace(on_node_event, node="resolve_targets", phase="error", state={**state, **out})
            return out

    async def _process_items_node(state: AutopilotGraphState) -> AutopilotGraphState:
        _emit_trace(on_node_event, node="process_items", phase="start", state=state)
        try:
            out = await process_items(state)
            if out.get("error_code"):
                out = {**out, "failed_node": "process_items", "retry_target_node": "process_items"}
                _emit_trace(on_node_event, node="process_items", phase="error", state={**state, **out})
                return out
            _emit_trace(on_node_event, node="process_items", phase="end", state={**state, **out})
            await _maybe_checkpoint("process_items", state, out)
            return out
        except Exception as exc:
            out = _exception_error_state("process_items", str(exc), retryable=True)
            _emit_trace(on_node_event, node="process_items", phase="error", state={**state, **out})
            return out

    async def _approval_interrupt_node(state: AutopilotGraphState) -> AutopilotGraphState:
        _emit_trace(on_node_event, node="approval_interrupt", phase="start", state=state)
        try:
            from langgraph.errors import GraphInterrupt
            from langgraph.types import interrupt

            payload = {
                "kind": "autopilot_approval_gate",
                "run_id": state.get("run_id"),
                "user_id": state.get("user_id"),
            }
            resume_value = interrupt(payload)
            _emit_trace(on_node_event, node="approval_interrupt", phase="end", state=state)
            out: AutopilotGraphState = {}
            if isinstance(resume_value, dict):
                out["approval_resume"] = resume_value  # type: ignore[typeddict-item]
                approved = resume_value.get("approved")
                if approved is False:
                    reason = str(
                        resume_value.get("rejection_reason")
                        or "Approval rejected by user"
                    )[:500]
                    out["error_code"] = "approval_rejected"
                    out["error_detail"] = reason
                    out["failed_node"] = "approval_interrupt"
                    out["retryable_error"] = False
                    out["retry_target_node"] = "approval_interrupt"
            return out
        except GraphInterrupt:
            raise
        except Exception as exc:
            out = _exception_error_state("approval_interrupt", str(exc), retryable=False)
            out = {**out, "failed_node": "approval_interrupt", "retry_target_node": "approval_interrupt"}
            _emit_trace(on_node_event, node="approval_interrupt", phase="error", state={**state, **out})
            return out

    async def _persist_done_node(state: AutopilotGraphState) -> AutopilotGraphState:
        _emit_trace(on_node_event, node="persist_done", phase="start", state=state)
        try:
            out = await persist_done(state)
            if out.get("error_code"):
                out = {**out, "failed_node": "persist_done", "retry_target_node": "persist_done"}
                _emit_trace(on_node_event, node="persist_done", phase="error", state={**state, **out})
                return out
            _emit_trace(on_node_event, node="persist_done", phase="end", state={**state, **out})
            return out
        except Exception as exc:
            out = _exception_error_state("persist_done", str(exc), retryable=False)
            _emit_trace(on_node_event, node="persist_done", phase="error", state={**state, **out})
            return out

    async def _recover_retry_node(state: AutopilotGraphState) -> AutopilotGraphState:
        _emit_trace(on_node_event, node="recover_retry", phase="start", state=state)
        out: AutopilotGraphState = {
            "retry_count": int(state.get("retry_count") or 0) + 1,
            "error_code": "",
            "error_detail": "",
            "retryable_error": False,
        }
        _emit_trace(on_node_event, node="recover_retry", phase="end", state={**state, **out})
        return out

    async def _persist_failed_node(state: AutopilotGraphState) -> AutopilotGraphState:
        _emit_trace(on_node_event, node="persist_failed", phase="start", state=state)
        try:
            out = await persist_failed(state)
            _emit_trace(on_node_event, node="persist_failed", phase="end", state={**state, **out})
            return out
        except Exception as exc:
            out: AutopilotGraphState = {
                "error_code": state.get("error_code") or "persist_failed_exception",
                "error_detail": state.get("error_detail") or str(exc)[:500],
                "failed_node": state.get("failed_node") or "persist_failed",
            }
            _emit_trace(on_node_event, node="persist_failed", phase="error", state={**state, **out})
            return out

    def _route_after_mark_running(state: AutopilotGraphState) -> str:
        if state.get("error_code"):
            return "persist_failed"
        if state.get("halt"):
            return END
        return "resolve_targets"

    def _route_after_resolve_targets(state: AutopilotGraphState) -> str:
        if state.get("error_code"):
            return "recover_retry" if _can_retry(state) else "persist_failed"
        return "process_items"

    def _route_after_process_items(state: AutopilotGraphState) -> str:
        if state.get("error_code"):
            return "recover_retry" if _can_retry(state) else "persist_failed"
        if approval_interrupt_enabled:
            return "approval_interrupt"
        return "persist_done"

    def _route_after_approval_interrupt(state: AutopilotGraphState) -> str:
        if state.get("error_code"):
            return "persist_failed"
        return "persist_done"

    def _route_after_persist_done(state: AutopilotGraphState) -> str:
        if state.get("error_code"):
            return "persist_failed"
        return END

    def _route_after_recover_retry(state: AutopilotGraphState) -> str:
        target = str(state.get("retry_target_node") or "")
        if target in {"resolve_targets", "process_items"}:
            return target
        return "persist_failed"

    def _route_graph_entry(state: AutopilotGraphState) -> str:
        entry = str(state.get("resume_entry_node") or "").strip()
        allowed = {"resolve_targets", "process_items", "persist_done"}
        if approval_interrupt_enabled:
            allowed = {*allowed, "approval_interrupt"}
        if entry in allowed:
            return entry
        return "mark_running"

    graph = StateGraph(AutopilotGraphState)
    graph.add_node("mark_running", _mark_running_node)
    graph.add_node("resolve_targets", _resolve_targets_node)
    graph.add_node("process_items", _process_items_node)
    graph.add_node("persist_done", _persist_done_node)
    graph.add_node("recover_retry", _recover_retry_node)
    graph.add_node("persist_failed", _persist_failed_node)
    if approval_interrupt_enabled:
        graph.add_node("approval_interrupt", _approval_interrupt_node)
    entry_map = {
        "mark_running": "mark_running",
        "resolve_targets": "resolve_targets",
        "process_items": "process_items",
        "persist_done": "persist_done",
    }
    if approval_interrupt_enabled:
        entry_map["approval_interrupt"] = "approval_interrupt"
    graph.add_conditional_edges(
        START,
        _route_graph_entry,
        entry_map,
    )
    graph.add_conditional_edges("mark_running", _route_after_mark_running)
    graph.add_conditional_edges("resolve_targets", _route_after_resolve_targets)
    graph.add_conditional_edges("process_items", _route_after_process_items)
    if approval_interrupt_enabled:
        graph.add_conditional_edges("approval_interrupt", _route_after_approval_interrupt)
    graph.add_conditional_edges("persist_done", _route_after_persist_done)
    graph.add_conditional_edges("recover_retry", _route_after_recover_retry)
    graph.add_edge("persist_failed", END)
    if approval_interrupt_enabled:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


async def run_autopilot_via_langgraph(
    *,
    initial_state: AutopilotGraphState | None = None,
    resume_command: Any | None = None,
    graph_invoke_config: dict[str, Any] | None = None,
    approval_interrupt_enabled: bool = False,
    mark_running: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    resolve_targets: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    process_items: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    persist_done: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    persist_failed: Callable[[AutopilotGraphState], Awaitable[AutopilotGraphState]],
    on_node_event: Callable[[AutopilotGraphTraceEvent], None] | None = None,
    on_node_checkpoint: Callable[[str, AutopilotGraphState], Awaitable[None]] | None = None,
) -> dict[str, Any]:
    """Execute existing autopilot behavior through explicit LangGraph parity nodes.

    When ``approval_interrupt_enabled`` and using a checkpointer, pass ``graph_invoke_config`` with
    ``{"configurable": {"thread_id": "<run_id>"}}``. For human resume after ``interrupt()``, call again with
    ``resume_command=Command(resume=...)`` and the same ``graph_invoke_config`` (same worker process).
    """
    checkpointer = await get_autopilot_langgraph_checkpointer() if approval_interrupt_enabled else None
    app = _build_autopilot_parity_graph(
        mark_running=mark_running,
        resolve_targets=resolve_targets,
        process_items=process_items,
        persist_done=persist_done,
        persist_failed=persist_failed,
        on_node_event=on_node_event,
        on_node_checkpoint=on_node_checkpoint,
        approval_interrupt_enabled=approval_interrupt_enabled,
        checkpointer=checkpointer,
    )
    cfg = graph_invoke_config
    if resume_command is not None:
        out = await app.ainvoke(resume_command, cfg) if cfg else await app.ainvoke(resume_command)
    elif cfg:
        out = await app.ainvoke(initial_state or {}, cfg)
    else:
        out = await app.ainvoke(initial_state or {})
    return cast(dict[str, Any], out)
