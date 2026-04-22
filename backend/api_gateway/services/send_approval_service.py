"""Outbound send after approval — SMTP when configured; otherwise durable state only."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import SessionLocal, bind_request_user_for_rls, reset_request_user_rls
from models.application import Application
from models.approval import Approval
from models.google_oauth_credential import GoogleOAuthCredential
from models.job import Job
from models.user import User
from services.gmail_send_service import create_gmail_draft, send_gmail_message
from services.outbound_email import send_email_outbound

logger = logging.getLogger(__name__)


async def execute_approval_send_stub(session: AsyncSession, approval_id: str, user_id: str) -> None:
    approval = (
        await session.execute(select(Approval).where(Approval.id == approval_id, Approval.user_id == user_id))
    ).scalar_one_or_none()
    if approval is None:
        logger.warning("send_stub: approval %s not found for user %s", approval_id, user_id)
        return
    if approval.status not in ("approved", "edited"):
        logger.warning("send_stub: approval %s status=%s", approval_id, approval.status)
        return

    app_row = await session.get(Application, approval.application_id)
    if app_row is None or app_row.user_id != user_id:
        logger.warning("send_stub: application missing or wrong user")
        return

    user = await session.get(User, user_id)
    if user is None:
        logger.warning("send_stub: user %s missing", user_id)
        return

    job = await session.get(Job, app_row.job_id)

    recipient = settings.outbound_send_recipient_override or user.email
    subject = approval.subject or (f"Application — {job.title}" if job else "Application")

    try:
        if approval.channel == "email":
            gmail_row = (
                await session.execute(select(GoogleOAuthCredential).where(GoogleOAuthCredential.user_id == user_id))
            ).scalar_one_or_none()
            sent_via_gmail = False
            if gmail_row is not None and settings.google_oauth_is_configured() and gmail_row.google_email:
                body_text = approval.draft_body or ""
                handoff = (settings.gmail_approval_handoff or "draft").strip().lower()
                try:
                    if handoff == "draft":
                        try:
                            await create_gmail_draft(
                                refresh_token_encrypted=gmail_row.refresh_token_encrypted,
                                from_addr=gmail_row.google_email,
                                to_addr=recipient,
                                subject=subject,
                                body=body_text,
                            )
                            sent_via_gmail = True
                        except Exception:
                            logger.exception(
                                "send_stub: gmail draft failed approval_id=%s; falling back to gmail send",
                                approval_id,
                            )
                            await send_gmail_message(
                                refresh_token_encrypted=gmail_row.refresh_token_encrypted,
                                from_addr=gmail_row.google_email,
                                to_addr=recipient,
                                subject=subject,
                                body=body_text,
                            )
                            sent_via_gmail = True
                    else:
                        await send_gmail_message(
                            refresh_token_encrypted=gmail_row.refresh_token_encrypted,
                            from_addr=gmail_row.google_email,
                            to_addr=recipient,
                            subject=subject,
                            body=body_text,
                        )
                        sent_via_gmail = True
                except Exception:
                    logger.exception(
                        "send_stub: gmail failed approval_id=%s user_id=%s; falling back to SMTP/dry-run",
                        approval_id,
                        user_id,
                    )
            if not sent_via_gmail:
                await send_email_outbound(to_addr=recipient, subject=subject, body=approval.draft_body)
        else:
            logger.info(
                "send_stub: channel=%s has no SMTP integration; recording sent locally only",
                approval.channel,
            )
    except Exception:
        logger.exception("send_stub: outbound dispatch failed approval_id=%s", approval_id)
        return

    now = datetime.now(timezone.utc)
    approval.sent_at = now
    app_row.status = "applied"
    app_row.applied_at = now
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
