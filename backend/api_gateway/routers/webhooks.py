"""Server-to-server endpoints (shared secrets)."""

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_session
from schemas.webhooks import ProfileImpressionWebhookIn, ProfileImpressionWebhookResponse
from services.profile_views_service import increment_profile_views

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_profile_impression_secret(x_webhook_secret: str | None) -> None:
    expected = settings.profile_impression_webhook_secret
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Profile impression webhook is not configured (PROFILE_IMPRESSION_WEBHOOK_SECRET)",
        )
    if not x_webhook_secret:
        raise HTTPException(status_code=403, detail="Missing X-Webhook-Secret header")
    if not hmac.compare_digest(x_webhook_secret.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")


@router.post("/profile-impression", response_model=ProfileImpressionWebhookResponse)
async def ingest_profile_impression(
    payload: ProfileImpressionWebhookIn,
    session: AsyncSession = Depends(get_session),
    x_webhook_secret: Annotated[str | None, Header(alias="X-Webhook-Secret")] = None,
) -> ProfileImpressionWebhookResponse:
    """
    Increment ``users.profile_views`` for integrations that observe recruiter/employer views.

    Authenticate with header ``X-Webhook-Secret`` matching ``PROFILE_IMPRESSION_WEBHOOK_SECRET``.
    """
    _verify_profile_impression_secret(x_webhook_secret)
    try:
        total = await increment_profile_views(session, payload.user_id, delta=payload.count)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ProfileImpressionWebhookResponse(profile_views=total)
