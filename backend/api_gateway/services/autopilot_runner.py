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


def _error_suggests_gmail_send(error: str | None) -> bool:
    """Heuristic for ``gmail_failed_only`` retries (errors that look Gmail/API related)."""
    if not error:
        return False
    e = error.lower()
    needles = ("gmail", "google", "oauth", "compose", "credentials", "token", "403", "401", "gmail.send")
    return any(n in e for n in needles)


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
    run_row = await session.get(AutopilotRun, run_id)
    if run_row is None or run_row.user_id != user_id:
        logger.warning("autopilot: run %s missing or wrong user", run_id)
        return

    run_row.status = "running"
    await session.commit()
    await session.refresh(run_row)

    scope = run_row.scope or "all"
    app_ids = await _resolve_target_application_ids(
        session,
        user_id=user_id,
        scope=scope,
        application_ids=application_ids,
    )

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
