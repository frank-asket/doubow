from pydantic import BaseModel, Field


class ProfileImpressionWebhookIn(BaseModel):
    """Called by ATS/analytics workers (not the candidate app) to record employer-side impressions."""

    user_id: str = Field(..., min_length=1)
    count: int = Field(default=1, ge=1, le=10_000)


class ProfileImpressionWebhookResponse(BaseModel):
    profile_views: int
