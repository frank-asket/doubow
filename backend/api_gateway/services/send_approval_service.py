"""Outbound send after approval with provider-confirmed delivery metadata."""

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
from models.linkedin_oauth_credential import LinkedInOAuthCredential
from models.user import User
from services.gmail_send_service import create_gmail_draft, send_gmail_message
from services.outbound_email import send_email_outbound

logger = logging.getLogger(__name__)


async def _send_user_confirmation(
    *,
    user_email: str,
    sender_email: str | None,
    via_gmail_token: str | None,
    subject: str,
    provider: str,
    provider_message_id: str | None,
) -> None:
    """Send a confirmation copy to the user's inbox after successful dispatch."""
    confirm_subject = f"Delivery confirmation: {subject}"
    confirm_body = (
        "Your outbound application message was dispatched.\n\n"
        f"Provider: {provider}\n"
        f"Provider message id: {provider_message_id or '(not available)'}\n"
        f"Original subject: {subject}\n"
    )
    if via_gmail_token and sender_email:
        try:
            await send_gmail_message(
                refresh_token_encrypted=via_gmail_token,
                from_addr=sender_email,
                to_addr=user_email,
                subject=confirm_subject,
                body=confirm_body,
            )
            return
        except Exception:
            logger.exception("send_stub: gmail confirmation copy failed; falling back to SMTP")
    await send_email_outbound(to_addr=user_email, subject=confirm_subject, body=confirm_body)


def _job_listing_url(job: Job | None) -> str:
    if job is None:
        return ""
    for candidate in (job.canonical_url, job.url):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


async def _send_linkedin_handoff_email(
    *,
    to_addr: str,
    job: Job | None,
    draft_body: str,
    linkedin_account_connected: bool,
) -> None:
    """Email the candidate a copy-paste pack; LinkedIn has no public API for automated DMs to recruiters."""
    company = (job.company.strip() if job and job.company else "the employer") or "the employer"
    title = (job.title.strip() if job and job.title else "the role") or "the role"
    listing = _job_listing_url(job)
    subject = f"Doubow: LinkedIn message for {company} — {title}"
    lines: list[str] = [
        "You approved this LinkedIn outreach in Doubow.",
        "",
        "LinkedIn does not offer a supported API for third-party apps to send connection notes or InMail on your behalf,",
        "so Doubow emails you the approved text to paste on the posting or in LinkedIn.",
        "",
    ]
    if linkedin_account_connected:
        lines.extend(
            [
                "Your LinkedIn account is linked in Doubow (profile sync and future integrations).",
                "",
            ]
        )
    lines.extend(
        [
            f"Role: {title}",
            f"Company: {company}",
            f"Posting / apply link: {listing or '(open the job in LinkedIn from Discover and paste there)'}",
            "",
            "——— Message to paste ———",
            draft_body.strip() or "(empty draft)",
            "———",
            "",
            "Tip: open the posting in LinkedIn, use Easy Apply or Message where available, paste the block above, then send.",
            "",
            "— Doubow",
        ]
    )
    body = "\n".join(lines)
    await send_email_outbound(to_addr=to_addr, subject=subject, body=body)


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

    # NOTE: Today this uses user email (or override) as recipient.
    # A dedicated recruiter-recipient source should replace this for real applications.
    recipient = settings.outbound_send_recipient_override or user.email
    subject = approval.subject or (f"Application — {job.title}" if job else "Application")
    now = datetime.now(timezone.utc)
    approval.delivery_status = "queued"
    approval.delivery_error = None
    confirmation_pending = False
    confirmation_sender_email: str | None = None
    confirmation_token: str | None = None

    def _annotate_application_progress(note: str) -> None:
        # Trust semantics: outbound dispatch/handoff is not an employer application submission.
        # Keep status unchanged, but record operational progression and touch last_updated.
        app_row.last_updated = now
        prior = (app_row.notes or "").strip()
        app_row.notes = f"{prior}\n{note}".strip() if prior else note

    try:
        if approval.channel == "email":
            gmail_row = (
                await session.execute(select(GoogleOAuthCredential).where(GoogleOAuthCredential.user_id == user_id))
            ).scalar_one_or_none()
            sent_via_gmail = False
            gmail_sender_email: str | None = None
            gmail_token: str | None = None
            if gmail_row is not None and settings.google_oauth_is_configured() and gmail_row.google_email:
                gmail_sender_email = gmail_row.google_email
                gmail_token = gmail_row.refresh_token_encrypted
                body_text = approval.draft_body or ""
                handoff = (settings.gmail_approval_handoff or "draft").strip().lower()
                try:
                    if handoff == "draft":
                        try:
                            draft_id = await create_gmail_draft(
                                refresh_token_encrypted=gmail_row.refresh_token_encrypted,
                                from_addr=gmail_row.google_email,
                                to_addr=recipient,
                                subject=subject,
                                body=body_text,
                            )
                            approval.send_provider = "gmail"
                            approval.delivery_status = "draft_created"
                            approval.provider_message_id = draft_id or None
                            approval.provider_thread_id = None
                            approval.provider_confirmed_at = None
                            approval.delivery_error = None
                            # Draft created successfully; still send user confirmation copy.
                            _annotate_application_progress("outreach:draft_created:gmail")
                            confirmation_pending = True
                            confirmation_sender_email = gmail_sender_email
                            confirmation_token = gmail_token
                        except Exception:
                            logger.exception(
                                "send_stub: gmail draft failed approval_id=%s; falling back to gmail send",
                                approval_id,
                            )
                            send_res = await send_gmail_message(
                                refresh_token_encrypted=gmail_row.refresh_token_encrypted,
                                from_addr=gmail_row.google_email,
                                to_addr=recipient,
                                subject=subject,
                                body=body_text,
                            )
                            sent_via_gmail = True
                            approval.send_provider = "gmail"
                            approval.delivery_status = "provider_confirmed"
                            approval.provider_message_id = send_res.get("id") or None
                            approval.provider_thread_id = send_res.get("threadId") or None
                            approval.provider_confirmed_at = now
                            approval.sent_at = now
                            _annotate_application_progress("outreach:provider_confirmed:gmail")
                            confirmation_pending = True
                            confirmation_sender_email = gmail_sender_email
                            confirmation_token = gmail_token
                    else:
                        send_res = await send_gmail_message(
                            refresh_token_encrypted=gmail_row.refresh_token_encrypted,
                            from_addr=gmail_row.google_email,
                            to_addr=recipient,
                            subject=subject,
                            body=body_text,
                        )
                        sent_via_gmail = True
                        approval.send_provider = "gmail"
                        approval.delivery_status = "provider_confirmed"
                        approval.provider_message_id = send_res.get("id") or None
                        approval.provider_thread_id = send_res.get("threadId") or None
                        approval.provider_confirmed_at = now
                        approval.sent_at = now
                        _annotate_application_progress("outreach:provider_confirmed:gmail")
                        confirmation_pending = True
                        confirmation_sender_email = gmail_sender_email
                        confirmation_token = gmail_token
                except Exception:
                    logger.exception(
                        "send_stub: gmail failed approval_id=%s user_id=%s; falling back to SMTP/dry-run",
                        approval_id,
                        user_id,
                    )
                    approval.delivery_error = "gmail_send_failed_fallback_to_smtp"
            if not sent_via_gmail:
                await send_email_outbound(to_addr=recipient, subject=subject, body=approval.draft_body)
                approval.send_provider = "smtp"
                approval.delivery_status = "provider_accepted"
                approval.provider_message_id = None
                approval.provider_thread_id = None
                approval.provider_confirmed_at = None
                approval.sent_at = now
                _annotate_application_progress("outreach:provider_accepted:smtp")
                confirmation_pending = True
                confirmation_sender_email = None
                confirmation_token = None
        elif approval.channel == "linkedin":
            li_row = (
                await session.execute(select(LinkedInOAuthCredential).where(LinkedInOAuthCredential.user_id == user_id))
            ).scalar_one_or_none()
            linkedin_connected = li_row is not None
            handoff_to = settings.outbound_send_recipient_override or user.email
            try:
                await _send_linkedin_handoff_email(
                    to_addr=handoff_to,
                    job=job,
                    draft_body=approval.draft_body or "",
                    linkedin_account_connected=linkedin_connected,
                )
            except Exception:
                logger.exception(
                    "send_stub: linkedin handoff email failed approval_id=%s user_id=%s",
                    approval_id,
                    user_id,
                )
                approval.delivery_status = "failed"
                approval.delivery_error = "linkedin_handoff_email_failed"
                await session.commit()
                return
            approval.send_provider = "linkedin_email_handoff"
            approval.delivery_status = "provider_confirmed"
            approval.provider_message_id = None
            approval.provider_thread_id = None
            approval.provider_confirmed_at = now
            approval.sent_at = now
            approval.delivery_error = None
            _annotate_application_progress("outreach:provider_confirmed:linkedin_email_handoff")
        else:
            logger.info(
                "send_stub: channel=%s has no SMTP integration; recording sent locally only",
                approval.channel,
            )
            approval.send_provider = "internal"
            approval.delivery_status = "provider_accepted"
            approval.provider_message_id = None
            approval.provider_thread_id = None
            approval.provider_confirmed_at = None
            approval.sent_at = now
            _annotate_application_progress("outreach:provider_accepted:internal")
    except Exception:
        logger.exception("send_stub: outbound dispatch failed approval_id=%s", approval_id)
        approval.delivery_status = "failed"
        approval.delivery_error = "dispatch_failed"
        _annotate_application_progress("outreach:failed:dispatch_failed")
        await session.commit()
        return

    if confirmation_pending:
        try:
            await _send_user_confirmation(
                user_email=user.email,
                sender_email=confirmation_sender_email,
                via_gmail_token=confirmation_token,
                subject=subject,
                provider=approval.send_provider or "smtp",
                provider_message_id=approval.provider_message_id,
            )
        except Exception:
            # Do not downgrade a successful dispatch solely because confirmation proof failed.
            logger.exception("send_stub: confirmation copy failed approval_id=%s", approval_id)
            approval.delivery_error = (
                f"{approval.delivery_error};confirmation_copy_failed"
                if approval.delivery_error
                else "confirmation_copy_failed"
            )

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
