"""Send email via Gmail API using a stored OAuth2 refresh token."""

from __future__ import annotations

import asyncio
import base64
import logging
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import settings
from services.google_token_crypto import GoogleTokenCryptoError, decrypt_refresh_token

logger = logging.getLogger(__name__)

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
# Create drafts in the user's mailbox (requires reconnect after adding this scope).
GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
GMAIL_API_SCOPES = [GMAIL_SEND_SCOPE, GMAIL_COMPOSE_SCOPE]


def _build_credentials(*, refresh_token_plain: str) -> Credentials:
    return Credentials(
        token=None,
        refresh_token=refresh_token_plain,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        scopes=list(GMAIL_API_SCOPES),
    )


def _send_raw_sync(*, refresh_token_plain: str, from_addr: str, to_addr: str, subject: str, body: str) -> None:
    creds = _build_credentials(refresh_token_plain=refresh_token_plain)
    creds.refresh(Request())

    mime = MIMEText(body, "plain", "utf-8")
    mime["To"] = to_addr
    mime["From"] = from_addr
    mime["Subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii")

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _create_draft_raw_sync(*, refresh_token_plain: str, from_addr: str, to_addr: str, subject: str, body: str) -> str:
    creds = _build_credentials(refresh_token_plain=refresh_token_plain)
    creds.refresh(Request())

    mime = MIMEText(body, "plain", "utf-8")
    mime["To"] = to_addr
    mime["From"] = from_addr
    mime["Subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii")

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    created = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    draft_id = created.get("id") if isinstance(created, dict) else None
    return str(draft_id or "")


async def create_gmail_draft(
    *,
    refresh_token_encrypted: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
) -> str:
    """Create a Gmail draft (user edits and sends from their inbox). Returns draft id when present."""
    try:
        refresh_plain = decrypt_refresh_token(refresh_token_encrypted)
    except GoogleTokenCryptoError:
        logger.exception("gmail draft: decrypt failed")
        raise

    draft_id = await asyncio.to_thread(
        _create_draft_raw_sync,
        refresh_token_plain=refresh_plain,
        from_addr=from_addr,
        to_addr=to_addr,
        subject=subject,
        body=body,
    )
    logger.info("gmail draft ok draft_id=%s to=%s subject=%s", draft_id, to_addr, subject[:120])
    return draft_id


async def send_gmail_message(
    *,
    refresh_token_encrypted: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
) -> bool:
    """Send one message as the connected Gmail account."""
    try:
        refresh_plain = decrypt_refresh_token(refresh_token_encrypted)
    except GoogleTokenCryptoError:
        logger.exception("gmail send: decrypt failed")
        raise

    await asyncio.to_thread(
        _send_raw_sync,
        refresh_token_plain=refresh_plain,
        from_addr=from_addr,
        to_addr=to_addr,
        subject=subject,
        body=body,
    )
    logger.info("gmail send ok to=%s subject=%s", to_addr, subject[:120])
    return True
