"""Execute queued autopilot runs: generate drafts per application (durable rows + item_results)."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import SessionLocal, bind_request_user_for_rls, reset_request_user_rls
from models.application import Application
from models.autopilot_run import AutopilotRun
from schemas.autopilot import AutopilotRunItem
from services.draft_service import create_draft_approval_for_application

logger = logging.getLogger(__name__)


async def _execute_autopilot_body(
    session: AsyncSession,
    *,
    run_id: str,
    user_id: str,
    application_ids: list[str] | None,
) -> None:
    run_row = await session.get(AutopilotRun, run_id)
    if run_row is None or run_row.user_id != user_id:
        logger.warning("autopilot: run %s missing or wrong user", run_id)
        return

    run_row.status = "running"
    await session.commit()
    await session.refresh(run_row)

    stmt = select(Application.id).where(Application.user_id == user_id)
    if application_ids:
        stmt = stmt.where(Application.id.in_(application_ids))
    # Scope failed_only / gmail_failed_only → not yet modeled; treat as all for now.
    app_id_rows = (await session.execute(stmt.order_by(Application.last_updated.desc()).limit(100))).all()
    app_ids = [r[0] for r in app_id_rows]

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

    run_row = await session.get(AutopilotRun, run_id)
    if run_row is None:
        return
    run_row.status = "done"
    run_row.item_results = item_payload
    run_row.completed_at = datetime.now(timezone.utc)
    await session.commit()


async def execute_autopilot_run_background(
    run_id: str,
    user_id: str,
    _scope: str,
    application_ids: list[str] | None,
) -> None:
    token = bind_request_user_for_rls(user_id)
    try:
        async with SessionLocal() as session:
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
                    row.completed_at = datetime.now(timezone.utc)
                    await session.commit()
        except Exception:
            logger.exception("autopilot failed to persist failure state run_id=%s", run_id)
    finally:
        reset_request_user_rls(token)
