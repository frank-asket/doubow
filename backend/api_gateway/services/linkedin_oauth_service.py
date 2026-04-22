"""LinkedIn OAuth helpers (authorize URL + code exchange)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from config import settings

LINKEDIN_SCOPES = ("openid", "profile", "email", "w_member_social")


def build_authorization_url(*, state: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.linkedin_oauth_client_id or "",
            "redirect_uri": settings.linkedin_oauth_redirect_uri or "",
            "state": state,
            "scope": " ".join(LINKEDIN_SCOPES),
        }
    )
    return f"https://www.linkedin.com/oauth/v2/authorization?{query}"


def exchange_code_for_access_token(*, code: str) -> tuple[str, datetime | None]:
    response = httpx.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.linkedin_oauth_redirect_uri or "",
            "client_id": settings.linkedin_oauth_client_id or "",
            "client_secret": settings.linkedin_oauth_client_secret or "",
        },
        timeout=15.0,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("LinkedIn did not return an access token")

    expires_at: datetime | None = None
    expires_in = payload.get("expires_in")
    if isinstance(expires_in, int) and expires_in > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return token, expires_at
