"""Enqueue autopilot resume for stuck LangGraph runs (checkpoint present)."""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.autopilot_run import AutopilotRun

_resume_lock = asyncio.Lock()
_inflight_resume_run_ids: set[str] = set()


def release_resume_slot(run_id: str) -> None:
    _inflight_resume_run_ids.discard(run_id)


async def try_acquire_resume_slot(run_id: str) -> bool:
    async with _resume_lock:
        if run_id in _inflight_resume_run_ids:
            return False
        _inflight_resume_run_ids.add(run_id)
        return True


async def validate_resume_eligibility(
    session: AsyncSession,
    *,
    user_id: str,
    run_id: str,
) -> tuple[AutopilotRun | None, str]:
    """Return ``(row, "")`` when resume is allowed; otherwise ``(None, reason)``."""
    row = await session.get(AutopilotRun, run_id)
    if row is None or row.user_id != user_id:
        return None, "Run not found"
    if row.status != "running":
        return None, f"Run is not running (status={row.status})"
    ck = row.graph_checkpoint if isinstance(row.graph_checkpoint, dict) else {}
    if ck.get("interrupt_pending"):
        return row, ""
    if settings.use_langgraph_autopilot and settings.use_langgraph_autopilot_checkpoint:
        if not row.graph_checkpoint:
            return None, "No graph checkpoint — resume only applies to LangGraph checkpointed runs"
    return row, ""
