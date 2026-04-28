from typing import Literal

from pydantic import BaseModel


class MeResponse(BaseModel):
    id: str
    email: str
    name: str
    plan: Literal["free", "pro"]


class MeDebugResponse(BaseModel):
    user_id: str
    auth_source: Literal["clerk_jwt"]


class EmailIdentityRow(BaseModel):
    user_id: str
    created_at: str | None = None


class MeEmailIdentityDebugResponse(BaseModel):
    email: str
    current_user_id: str
    ids_for_email: list[EmailIdentityRow]
    multiple_ids_for_same_email: bool


class MeAiConfigDebugResponse(BaseModel):
    openrouter_configured: bool
    openrouter_api_url: str
    openrouter_http_referer: str | None = None
    resolved_models: dict[str, str]


class OAuthProviderConfigDebug(BaseModel):
    configured: bool
    required_keys_present: dict[str, bool]
    missing_required_keys: list[str]


class MeOauthConfigDebugResponse(BaseModel):
    google: OAuthProviderConfigDebug
    linkedin: OAuthProviderConfigDebug
