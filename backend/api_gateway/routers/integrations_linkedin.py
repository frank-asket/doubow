"""LinkedIn account linking via OAuth2."""

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
from models.linkedin_oauth_credential import LinkedInOAuthCredential
from models.user import User
from services.google_oauth_state import sign_oauth_state, verify_oauth_state
from services.google_token_crypto import encrypt_refresh_token
from services.linkedin_oauth_service import build_authorization_url, exchange_code_for_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/linkedin", tags=["integrations-linkedin"])


@router.get("/authorize")
async def linkedin_authorize(user: User = Depends(get_authenticated_user)) -> dict[str, str]:
    if not settings.linkedin_oauth_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinkedIn OAuth is not configured on this server",
        )
    state = sign_oauth_state(user_id=user.id, secret=settings.linkedin_oauth_state_secret or "")
    return {"authorization_url": build_authorization_url(state=state)}


@router.get("/callback")
async def linkedin_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    base = settings.linkedin_oauth_frontend_redirect_uri.rstrip("/")

    def redirect_with(q: dict[str, str]) -> RedirectResponse:
        return RedirectResponse(f"{base}?{urlencode(q)}", status_code=status.HTTP_302_FOUND)

    if error:
        return redirect_with({"linkedin_error": error})
    if not code or not state:
        return redirect_with({"linkedin_error": "missing_code_or_state"})
    if not settings.linkedin_oauth_state_secret:
        return redirect_with({"linkedin_error": "server_misconfigured"})

    try:
        user_id = verify_oauth_state(token=state, secret=settings.linkedin_oauth_state_secret)
    except ValueError:
        return redirect_with({"linkedin_error": "invalid_state"})

    if not settings.linkedin_oauth_is_configured():
        return redirect_with({"linkedin_error": "server_misconfigured"})

    token = bind_request_user_for_rls(user_id)
    try:
        access_token, expires_at = exchange_code_for_access_token(code=code)
        enc = encrypt_refresh_token(access_token)
        row = await session.get(LinkedInOAuthCredential, user_id)
        if row is None:
            row = LinkedInOAuthCredential(user_id=user_id)
            session.add(row)
        row.access_token_encrypted = enc
        row.expires_at = expires_at
        await session.commit()
    except Exception:
        logger.exception("linkedin oauth callback failed user_id=%s", user_id)
        await session.rollback()
        return redirect_with({"linkedin_error": "token_exchange_failed"})
    finally:
        reset_request_user_rls(token)

    return redirect_with({"linkedin_connected": "1"})


@router.get("/status")
async def linkedin_status(
    user: User = Depends(get_authenticated_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    row = (
        await session.execute(select(LinkedInOAuthCredential).where(LinkedInOAuthCredential.user_id == user.id))
    ).scalar_one_or_none()
    return {
        "connected": row is not None,
        "expires_at": row.expires_at.isoformat() if row and row.expires_at else None,
    }


@router.delete("/")
async def linkedin_disconnect(
    user: User = Depends(get_authenticated_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    row = await session.get(LinkedInOAuthCredential, user.id)
    if row is not None:
        await session.delete(row)
        await session.commit()
    return {"ok": True}
