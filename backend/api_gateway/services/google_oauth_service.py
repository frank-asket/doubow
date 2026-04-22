"""Exchange authorization code for refresh token; resolve Google account email."""

from __future__ import annotations

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import settings
from services.gmail_send_service import GMAIL_SEND_SCOPE


def google_client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_oauth_redirect_uri],
        }
    }


def build_authorization_url(*, state: str) -> str:
    scopes = [GMAIL_SEND_SCOPE]
    flow = Flow.from_client_config(google_client_config(), scopes=scopes)
    flow.redirect_uri = settings.google_oauth_redirect_uri
    uri, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return uri


def exchange_code_for_refresh_and_email(*, code: str) -> tuple[str, str | None]:
    """Return (refresh_token, google_email). Email from Gmail profile."""
    scopes = [GMAIL_SEND_SCOPE]
    flow = Flow.from_client_config(google_client_config(), scopes=scopes)
    flow.redirect_uri = settings.google_oauth_redirect_uri
    flow.fetch_token(code=code)
    creds: Credentials = flow.credentials
    if not creds.refresh_token:
        raise RuntimeError("Google did not return a refresh token; try revoking app access and reconnecting.")

    google_email: str | None = None
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    if isinstance(profile, dict):
        raw = profile.get("emailAddress")
        if isinstance(raw, str) and raw:
            google_email = raw

    return creds.refresh_token, google_email
