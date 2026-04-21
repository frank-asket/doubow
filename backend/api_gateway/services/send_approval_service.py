"""Stub outbound send after approval — updates durable state (real provider hooks go here)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import SessionLocal, bind_request_user_for_rls, reset_request_user_rls
from models.application import Application
from models.approval import Approval

logger = logging.getLogger(__name__)


async def execute_approval_send_stub(session: AsyncSession, approval_id: str, user_id: str) -> None:
    """Mark approval sent and application applied (stub: no external API call)."""
    approval = (
        await session.execute(select(Approval).where(Approval.id == approval_id, Approval.user_id == user_id))
    ).scalar_one_or_none()
    if approval is None:
        logger.warning("send_stub: approval %s not found for user %s", approval_id, user_id)
        return
    if approval.status not in ("approved", "edited"):
        logger.warning("send_stub: approval %s status=%s", approval_id, approval.status)
        return

    app = await session.get(Application, approval.application_id)
    if app is None or app.user_id != user_id:
        logger.warning("send_stub: application missing or wrong user")
        return

    now = datetime.now(timezone.utc)
    approval.sent_at = now
    app.status = "applied"
    app.applied_at = now
    await session.commit()


async def run_send_stub_in_background(approval_id: str, user_id: str) -> None:
    """Open an isolated session with RLS context for background execution."""
    token = bind_request_user_for_rls(user_id)
    try:
        async with SessionLocal() as session:
            await execute_approval_send_stub(session, approval_id, user_id)
    except Exception:
        logger.exception("send_stub failed approval_id=%s user_id=%s", approval_id, user_id)
    finally:
        reset_request_user_rls(token)
