from datetime import datetime

from pydantic import BaseModel

from schemas.applications import Application


class PrepGenerateRequest(BaseModel):
    application_id: str


class PrepSessionDetailResponse(BaseModel):
    """Prep payload aligned with frontend ``PrepSession`` (nested application)."""

    id: str
    application: Application
    questions: list[str]
    star_stories: list[dict]
    company_brief: str
    created_at: datetime
