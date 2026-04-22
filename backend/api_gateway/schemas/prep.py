from datetime import datetime

from typing import Literal

from pydantic import BaseModel

from schemas.applications import Application


class PrepAssistRequest(BaseModel):
    application_id: str
    kind: Literal["company_brief", "star_story"]


class PrepAssistResponse(BaseModel):
    text: str


class PrepGenerateRequest(BaseModel):
    application_id: str


class PrepCapabilitiesResponse(BaseModel):
    assist_route_available: bool
    llm_configured: bool


class PrepSessionDetailResponse(BaseModel):
    """Prep payload aligned with frontend ``PrepSession`` (nested application)."""

    id: str
    application: Application
    questions: list[str]
    star_stories: list[dict]
    company_brief: str
    created_at: datetime
