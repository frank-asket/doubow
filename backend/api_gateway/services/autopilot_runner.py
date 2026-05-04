"""Execute queued autopilot runs: generate drafts per application (durable rows + item_results)."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import SessionLocal, bind_request_user_for_rls, reset_request_user_rls
from config import settings
from models.application import Application
from models.autopilot_run import AutopilotRun
from schemas.autopilot import AutopilotRunItem
from services.draft_service import create_draft_approval_for_application
from workflow.autopilot_langgraph import AutopilotGraphState

logger = logging.getLogger(__name__)

_CHECKPOINT_STATE_KEYS = frozenset(
    {
        "run_id",
        "user_id",
        "application_ids",
        "scope",
        "app_ids",
        "item_payload",
        "retry_count",
        "max_retries",
        "halt",
        "ok",
    }
)

def _next_resume_entry_after_node(completed_node: str) -> str | None:
    chain: dict[str, str] = {
        "mark_running": "resolve_targets",
        "resolve_targets": "process_items",
        "process_items": (
            "approval_interrupt"
            if settings.use_langgraph_autopilot_approval_interrupt
            else "persist_done"
        ),
        "approval_interrupt": "persist_done",
    }
    return chain.get(completed_node)


def _serialize_autopilot_checkpoint(merged: AutopilotGraphState, *, completed_node: str) -> dict[str, object]:
    st: dict[str, object] = {}
    for k in _CHECKPOINT_STATE_KEYS:
        if k in merged and merged[k] is not None:
            st[str(k)] = merged[k]
    return {
        "v": 1,
        "state": st,
        "next_resume_entry": _next_resume_entry_after_node(completed_node),
    }


async def _persist_autopilot_checkpoint(
    session: AsyncSession,
    *,
    run_id: str,
    merged: AutopilotGraphState,
    completed_node: str,
) -> None:
    row = await session.get(AutopilotRun, run_id)
    if row is None:
        return
    row.graph_checkpoint = _serialize_autopilot_checkpoint(merged, completed_node=completed_node)
    await session.commit()


async def _clear_autopilot_checkpoint(session: AsyncSession, *, run_id: str) -> None:
    row = await session.get(AutopilotRun, run_id)
    if row is None or row.graph_checkpoint is None:
        return
    row.graph_checkpoint = None
    await session.commit()


async def _persist_autopilot_interrupt_marker(
    session: AsyncSession,
    *,
    run_id: str,
    graph_out: dict[str, object],
) -> None:
    """Record that the LangGraph run is paused at ``interrupt()`` (human approval gate)."""
    row = await session.get(AutopilotRun, run_id)
    if row is None:
        return
    st: dict[str, object] = {}
    for k in _CHECKPOINT_STATE_KEYS:
        if k in graph_out and graph_out[k] is not None:
            st[str(k)] = graph_out[k]
    row.graph_checkpoint = {
        "v": 1,
        "state": st,
        "next_resume_entry": "approval_interrupt",
        "interrupt_pending": True,
    }
    await session.commit()


async def _build_initial_langgraph_state(
    session: AsyncSession,
    *,
    run_id: str,
    user_id: str,
    application_ids: list[str] | None,
) -> AutopilotGraphState:
    base: AutopilotGraphState = {
        "run_id": run_id,
        "user_id": user_id,
        "application_ids": application_ids,
        "retry_count": 0,
        "max_retries": max(0, settings.use_langgraph_autopilot_max_retries),
    }
    if not settings.use_langgraph_autopilot_checkpoint:
        return base
    row = await session.get(AutopilotRun, run_id)
    if row is None or not isinstance(row.graph_checkpoint, dict):
        return base
    ck = row.graph_checkpoint
    if ck.get("v") != 1 or not isinstance(ck.get("state"), dict):
        return base
    st_dict = dict(ck["state"])
    st_dict["run_id"] = run_id
    st_dict["user_id"] = user_id
    if application_ids is not None:
        st_dict["application_ids"] = application_ids
    nxt = ck.get("next_resume_entry")
    if isinstance(nxt, str) and nxt in (
        "resolve_targets",
        "process_items",
        "persist_done",
        "approval_interrupt",
    ):
        st_dict["resume_entry_node"] = nxt
    return st_dict  # type: ignore[return-value]


def _build_langgraph_trace_callback(*, run_id: str, user_id: str):
    def _trace(event: dict[str, object]) -> None:
        node = str(event.get("node") or "unknown")
        phase = str(event.get("phase") or "unknown")
        state = event.get("state")
        state_keys = sorted(state.keys()) if isinstance(state, dict) else []
        logger.info(
            "autopilot langgraph trace run_id=%s user_id=%s node=%s phase=%s state_keys=%s",
            run_id,
            user_id,
            node,
            phase,
            state_keys,
        )

    return _trace


def _error_suggests_gmail_send(error: str | None) -> bool:
    """Heuristic for ``gmail_failed_only`` retries (errors that look Gmail/API related)."""
    if not error:
        return False
    e = error.lower()
    needles = ("gmail", "google", "oauth", "compose", "credentials", "token", "403", "401", "gmail.send")
    return any(n in e for n in needles)


def _is_transient_error(exc: Exception) -> bool:
    e = str(exc).lower()
    transient_needles = ("timeout", "temporar", "connection", "rate limit", "429", "503", "502", "504")
    return any(n in e for n in transient_needles)


def _failed_application_ids_from_results(item_results: list | None) -> list[str]:
    if not item_results:
        return []
    out: list[str] = []
    for it in item_results:
        if not isinstance(it, dict):
            continue
        if it.get("status") == "failed" and it.get("application_id"):
            out.append(str(it["application_id"]))
    return out


def _gmail_failed_application_ids_from_results(item_results: list | None) -> list[str]:
    if not item_results:
        return []
    out: list[str] = []
    for it in item_results:
        if not isinstance(it, dict) or it.get("status") != "failed":
            continue
        err = it.get("error")
        es = err if isinstance(err, str) else None
        if _error_suggests_gmail_send(es) and it.get("application_id"):
            out.append(str(it["application_id"]))
    return out


async def _latest_prior_done_run(session: AsyncSession, user_id: str) -> AutopilotRun | None:
    """Most recent completed run with item_results (used for retry scopes)."""
    return (
        await session.execute(
            select(AutopilotRun)
            .where(
                AutopilotRun.user_id == user_id,
                AutopilotRun.status == "done",
                AutopilotRun.item_results.isnot(None),
            )
            .order_by(AutopilotRun.completed_at.desc().nulls_last(), AutopilotRun.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _resolve_target_application_ids(
    session: AsyncSession,
    *,
    user_id: str,
    scope: str,
    application_ids: list[str] | None,
) -> list[str]:
    scope_norm = (scope or "all").strip().lower()

    raw_candidates: list[str]
    if scope_norm == "failed_only":
        prior = await _latest_prior_done_run(session, user_id)
        if prior is None:
            logger.info("autopilot scope=failed_only: no prior completed run with results")
            return []
        raw_candidates = _failed_application_ids_from_results(prior.item_results)
    elif scope_norm == "gmail_failed_only":
        prior = await _latest_prior_done_run(session, user_id)
        if prior is None:
            logger.info("autopilot scope=gmail_failed_only: no prior completed run with results")
            return []
        raw_candidates = _gmail_failed_application_ids_from_results(prior.item_results)
        if not raw_candidates:
            logger.info("autopilot scope=gmail_failed_only: no failed items with Gmail-related errors")
            return []
    else:
        stmt = select(Application.id).where(Application.user_id == user_id)
        if application_ids:
            stmt = stmt.where(Application.id.in_(application_ids))
        rows = (await session.execute(stmt.order_by(Application.last_updated.desc()).limit(100))).all()
        return [r[0] for r in rows]

    if not raw_candidates:
        return []

    stmt = select(Application.id).where(Application.user_id == user_id, Application.id.in_(raw_candidates))
    if application_ids:
        stmt = stmt.where(Application.id.in_(application_ids))
    rows = (await session.execute(stmt.order_by(Application.last_updated.desc()).limit(100))).all()
    return [r[0] for r in rows]


async def _execute_autopilot_body(
    session: AsyncSession,
    *,
    run_id: str,
    user_id: str,
    application_ids: list[str] | None,
) -> None:
    has_run, scope = await _mark_run_running(
        session=session,
        run_id=run_id,
        user_id=user_id,
    )
    if not has_run:
        return

    app_ids = await _resolve_target_app_ids_for_run(
        session=session,
        user_id=user_id,
        scope=scope,
        application_ids=application_ids,
    )
    item_payload = await _process_autopilot_items(
        session=session,
        user_id=user_id,
        app_ids=app_ids,
    )
    await _persist_run_done(
        session=session,
        run_id=run_id,
        item_payload=item_payload,
    )


async def _mark_run_running(
    session: AsyncSession,
    *,
    run_id: str,
    user_id: str,
) -> tuple[bool, str]:
    run_row = await session.get(AutopilotRun, run_id)
    if run_row is None or run_row.user_id != user_id:
        logger.warning("autopilot: run %s missing or wrong user", run_id)
        return False, "all"

    run_row.status = "running"
    run_row.failure_code = None
    run_row.failure_detail = None
    run_row.failure_node = None
    await session.commit()
    await session.refresh(run_row)
    return True, run_row.scope or "all"


async def _resolve_target_app_ids_for_run(
    session: AsyncSession,
    *,
    user_id: str,
    scope: str,
    application_ids: list[str] | None,
) -> list[str]:
    return await _resolve_target_application_ids(
        session,
        user_id=user_id,
        scope=scope,
        application_ids=application_ids,
    )


async def _process_autopilot_items(
    session: AsyncSession,
    *,
    user_id: str,
    app_ids: list[str],
) -> list[dict]:
    item_payload: list[dict] = []
    for app_id in app_ids:
        t0 = time.perf_counter()
        try:
            await create_draft_approval_for_application(session, user_id, app_id)
            ms = max(0, int((time.perf_counter() - t0) * 1000))
            item_payload.append(
                AutopilotRunItem(
                    application_id=app_id,
                    status="success",
                    retryable=False,
                    suggested_action=None,
                    latency_ms=ms,
                    error=None,
                ).model_dump()
            )
        except Exception as exc:
            ms = max(0, int((time.perf_counter() - t0) * 1000))
            logger.exception("autopilot item failed app_id=%s", app_id)
            item_payload.append(
                AutopilotRunItem(
                    application_id=app_id,
                    status="failed",
                    retryable=True,
                    suggested_action="Retry draft generation or check application state",
                    latency_ms=ms,
                    error=str(exc)[:500],
                ).model_dump()
            )
    return item_payload


async def _persist_run_done(
    session: AsyncSession,
    *,
    run_id: str,
    item_payload: list[dict],
) -> None:
    run_row = await session.get(AutopilotRun, run_id)
    if run_row is None:
        return
    run_row.status = "done"
    run_row.item_results = item_payload
    run_row.failure_code = None
    run_row.failure_detail = None
    run_row.failure_node = None
    run_row.completed_at = datetime.now(timezone.utc)
    await session.commit()


async def _persist_run_failed(
    session: AsyncSession,
    *,
    run_id: str,
    error_code: str | None,
    error_detail: str | None,
    failed_node: str | None,
) -> None:
    run_row = await session.get(AutopilotRun, run_id)
    if run_row is None:
        return
    run_row.status = "failed"
    run_row.failure_code = (error_code or "unknown_error")[:64]
    run_row.failure_detail = (error_detail or "")[:500] or None
    run_row.failure_node = (failed_node or "unknown")[:64]
    run_row.completed_at = datetime.now(timezone.utc)
    await session.commit()
    logger.warning(
        "autopilot langgraph failed run_id=%s failed_node=%s error_code=%s error_detail=%s",
        run_id,
        failed_node or "unknown",
        error_code or "unknown",
        (error_detail or "")[:200],
    )


async def _run_autopilot_langgraph_invoke(
    session: AsyncSession,
    *,
    run_id: str,
    user_id: str,
    application_ids: list[str] | None,
    initial_state: AutopilotGraphState | None,
    resume_command: object | None = None,
) -> dict[str, object]:
    from workflow.autopilot_langgraph import run_autopilot_via_langgraph

    interrupt_on = bool(
        settings.use_langgraph_autopilot
        and settings.use_langgraph_autopilot_approval_interrupt
    )
    graph_cfg = (
        {"configurable": {"thread_id": run_id}}
        if interrupt_on
        else None
    )

    async def _on_node_checkpoint(node: str, merged: AutopilotGraphState) -> None:
        if not settings.use_langgraph_autopilot_checkpoint:
            return
        await _persist_autopilot_checkpoint(
            session,
            run_id=run_id,
            merged=merged,
            completed_node=node,
        )

    return await run_autopilot_via_langgraph(
        initial_state=initial_state,
        resume_command=resume_command,
        graph_invoke_config=graph_cfg,
        approval_interrupt_enabled=interrupt_on,
        mark_running=lambda state: _langgraph_mark_running_step(
            session=session,
            state=state,
        ),
        resolve_targets=lambda state: _langgraph_resolve_targets_step(
            session=session,
            state=state,
        ),
        process_items=lambda state: _langgraph_process_items_step(
            session=session,
            state=state,
        ),
        persist_done=lambda state: _langgraph_persist_done_step(
            session=session,
            state=state,
        ),
        persist_failed=lambda state: _langgraph_persist_failed_step(
            session=session,
            state=state,
        ),
        on_node_event=(
            _build_langgraph_trace_callback(run_id=run_id, user_id=user_id)
            if settings.use_langgraph_autopilot_trace
            else None
        ),
        on_node_checkpoint=_on_node_checkpoint if settings.use_langgraph_autopilot_checkpoint else None,
    )


async def execute_autopilot_run_background(
    run_id: str,
    user_id: str,
    application_ids: list[str] | None,
) -> None:
    token = bind_request_user_for_rls(user_id)
    try:
        async with SessionLocal() as session:
            row = await session.get(AutopilotRun, run_id)
            ck = row.graph_checkpoint if row and isinstance(row.graph_checkpoint, dict) else {}

            if (
                settings.use_langgraph_autopilot
                and ck.get("interrupt_pending")
                and row
                and row.user_id == user_id
            ):
                try:
                    from langgraph.types import Command

                    await _run_autopilot_langgraph_invoke(
                        session,
                        run_id=run_id,
                        user_id=user_id,
                        application_ids=application_ids,
                        initial_state=None,
                        resume_command=Command(resume={"approved": True}),
                    )
                except Exception:
                    logger.exception(
                        "autopilot langgraph approval-interrupt resume failed run_id=%s", run_id
                    )
                    await _persist_run_failed(
                        session,
                        run_id=run_id,
                        error_code="langgraph_interrupt_resume_failed",
                        error_detail="Could not resume interrupted graph (worker restart loses in-memory checkpoint)",
                        failed_node="approval_interrupt",
                    )
                return

            if settings.use_langgraph_autopilot:
                try:
                    initial_state = await _build_initial_langgraph_state(
                        session,
                        run_id=run_id,
                        user_id=user_id,
                        application_ids=application_ids,
                    )
                    out = await _run_autopilot_langgraph_invoke(
                        session,
                        run_id=run_id,
                        user_id=user_id,
                        application_ids=application_ids,
                        initial_state=initial_state,
                    )
                    if out.get("__interrupt__"):
                        await _persist_autopilot_interrupt_marker(
                            session,
                            run_id=run_id,
                            graph_out=out,
                        )
                except Exception:
                    logger.exception(
                        "autopilot langgraph wrapper failed; falling back to legacy run_id=%s", run_id
                    )
                    await _execute_autopilot_body(
                        session,
                        run_id=run_id,
                        user_id=user_id,
                        application_ids=application_ids,
                    )
            else:
                await _execute_autopilot_body(
                    session,
                    run_id=run_id,
                    user_id=user_id,
                    application_ids=application_ids,
                )
    except Exception:
        logger.exception("autopilot run failed run_id=%s", run_id)
        try:
            async with SessionLocal() as session:
                row = await session.get(AutopilotRun, run_id)
                if row and row.user_id == user_id:
                    row.status = "failed"
                    row.failure_code = "background_exception"
                    row.failure_detail = "Unhandled background exception during autopilot execution"
                    row.failure_node = "execute_autopilot_run_background"
                    row.completed_at = datetime.now(timezone.utc)
                    await session.commit()
        except Exception:
            logger.exception("autopilot failed to persist failure state run_id=%s", run_id)
    finally:
        reset_request_user_rls(token)


async def _langgraph_mark_running_step(
    *,
    session: AsyncSession,
    state: AutopilotGraphState,
) -> AutopilotGraphState:
    run_id = str(state.get("run_id") or "")
    user_id = str(state.get("user_id") or "")
    has_run, scope = await _mark_run_running(
        session=session,
        run_id=run_id,
        user_id=user_id,
    )
    return {"scope": scope, "halt": not has_run}


async def _langgraph_resolve_targets_step(
    *,
    session: AsyncSession,
    state: AutopilotGraphState,
) -> AutopilotGraphState:
    user_id = str(state.get("user_id") or "")
    scope = str(state.get("scope") or "all")
    application_ids = state.get("application_ids")
    typed_application_ids = application_ids if isinstance(application_ids, list) else None
    try:
        app_ids = await _resolve_target_app_ids_for_run(
            session=session,
            user_id=user_id,
            scope=scope,
            application_ids=typed_application_ids,
        )
        return {"app_ids": app_ids}
    except Exception as exc:
        return {
            "error_code": "resolve_targets_failed",
            "error_detail": str(exc)[:500],
            "retryable_error": _is_transient_error(exc),
        }


async def _langgraph_process_items_step(
    *,
    session: AsyncSession,
    state: AutopilotGraphState,
) -> AutopilotGraphState:
    user_id = str(state.get("user_id") or "")
    app_ids = state.get("app_ids")
    typed_app_ids = app_ids if isinstance(app_ids, list) else []
    try:
        item_payload = await _process_autopilot_items(
            session=session,
            user_id=user_id,
            app_ids=[str(app_id) for app_id in typed_app_ids],
        )
        return {"item_payload": item_payload}
    except Exception as exc:
        return {
            "error_code": "process_items_failed",
            "error_detail": str(exc)[:500],
            "retryable_error": _is_transient_error(exc),
        }


async def _langgraph_persist_done_step(
    *,
    session: AsyncSession,
    state: AutopilotGraphState,
) -> AutopilotGraphState:
    run_id = str(state.get("run_id") or "")
    item_payload = state.get("item_payload")
    typed_payload = item_payload if isinstance(item_payload, list) else []
    await _persist_run_done(
        session=session,
        run_id=run_id,
        item_payload=[it for it in typed_payload if isinstance(it, dict)],
    )
    await _clear_autopilot_checkpoint(session, run_id=run_id)
    return {"ok": True}


async def _langgraph_persist_failed_step(
    *,
    session: AsyncSession,
    state: AutopilotGraphState,
) -> AutopilotGraphState:
    run_id = str(state.get("run_id") or "")
    error_code = str(state.get("error_code") or "unknown_error")
    error_detail = str(state.get("error_detail") or "")
    failed_node = str(state.get("failed_node") or "unknown")
    await _persist_run_failed(
        session=session,
        run_id=run_id,
        error_code=error_code,
        error_detail=error_detail,
        failed_node=failed_node,
    )
    await _clear_autopilot_checkpoint(session, run_id=run_id)
    return {
        "ok": False,
        "error_code": error_code,
        "error_detail": error_detail,
        "failed_node": failed_node,
    }
