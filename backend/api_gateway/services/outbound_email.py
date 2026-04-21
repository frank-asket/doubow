"""SMTP outbound mail for approval sends (dry-run when SMTP is disabled)."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


def _send_smtp_sync(*, to_addr: str, subject: str, body: str) -> None:
    """Blocking SMTP send (invoked via asyncio.to_thread)."""
    assert settings.smtp_enabled and settings.outbound_from_email

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.outbound_from_email
    msg["To"] = to_addr
    msg.attach(MIMEText(body, "plain", "utf-8"))

    host = settings.smtp_host
    port = int(settings.smtp_port)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=60) as server:
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.outbound_from_email, [to_addr], msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=60) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.outbound_from_email, [to_addr], msg.as_string())


async def send_email_outbound(*, to_addr: str, subject: str, body: str) -> bool:
    """Send one plain-text email. Returns True when sent or intentionally skipped (dry-run)."""
    if not settings.smtp_enabled or not settings.outbound_from_email:
        logger.info(
            "outbound email dry-run (smtp disabled): to=%s subject=%s bytes=%s",
            to_addr,
            subject[:120],
            len(body.encode("utf-8")),
        )
        return True

    await asyncio.to_thread(_send_smtp_sync, to_addr=to_addr, subject=subject, body=body)
    logger.info("outbound email sent to=%s subject=%s", to_addr, subject[:120])
    return True
