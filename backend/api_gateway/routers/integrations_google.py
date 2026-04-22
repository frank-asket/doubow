"""Google account linking (Gmail send) via OAuth2."""

from __future__ import annotations

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import bind_request_user_for_rls, get_session, reset_request_user_rls
from dependencies import get_authenticated_user
from models.google_oauth_credential import GoogleOAuthCredential
from models.user import User
from services.gmail_send_service import GMAIL_API_SCOPES
from services.google_oauth_service import build_authorization_url, exchange_code_for_refresh_and_email
from services.google_oauth_state import sign_oauth_state, verify_oauth_state
from services.google_token_crypto import encrypt_refresh_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/google", tags=["integrations-google"])


@router.get("/authorize")
async def google_authorize(user: User = Depends(get_authenticated_user)) -> dict[str, str]:
    if not settings.google_oauth_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on this server",
        )
    state = sign_oauth_state(user_id=user.id, secret=settings.google_oauth_state_secret or "")
    url = build_authorization_url(state=state)
    return {"authorization_url": url}


@router.get("/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    base = settings.google_oauth_frontend_redirect_uri.rstrip("/")

    def redirect_with(q: dict[str, str]) -> RedirectResponse:
        return RedirectResponse(f"{base}?{urlencode(q)}", status_code=status.HTTP_302_FOUND)

    if error:
        return redirect_with({"google_error": error})
    if not code or not state:
        return redirect_with({"google_error": "missing_code_or_state"})
    if not settings.google_oauth_state_secret:
        return redirect_with({"google_error": "server_misconfigured"})

    try:
        user_id = verify_oauth_state(token=state, secret=settings.google_oauth_state_secret)
    except ValueError:
        return redirect_with({"google_error": "invalid_state"})

    if not settings.google_oauth_is_configured():
        return redirect_with({"google_error": "server_misconfigured"})

    token = bind_request_user_for_rls(user_id)
    try:
        refresh, gemail = exchange_code_for_refresh_and_email(code=code)
        enc = encrypt_refresh_token(refresh)
        row = await session.get(GoogleOAuthCredential, user_id)
        if row is None:
            row = GoogleOAuthCredential(user_id=user_id)
            session.add(row)
        row.refresh_token_encrypted = enc
        row.google_email = gemail
        row.scopes = " ".join(GMAIL_API_SCOPES)
        await session.commit()
    except Exception:
        logger.exception("google oauth callback failed user_id=%s", user_id)
        await session.rollback()
        return redirect_with({"google_error": "token_exchange_failed"})
    finally:
        reset_request_user_rls(token)

    return redirect_with({"google_connected": "1"})


@router.get("/status")
async def google_status(
    user: User = Depends(get_authenticated_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    row = (
        await session.execute(select(GoogleOAuthCredential).where(GoogleOAuthCredential.user_id == user.id))
    ).scalar_one_or_none()
    return {
        "connected": row is not None,
        "google_email": row.google_email if row else None,
    }


@router.delete("/")
async def google_disconnect(
    user: User = Depends(get_authenticated_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    row = await session.get(GoogleOAuthCredential, user.id)
    if row is not None:
        await session.delete(row)
        await session.commit()
    return {"ok": True}
