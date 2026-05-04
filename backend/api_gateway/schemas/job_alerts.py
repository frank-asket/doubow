from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

JobAlertFrequency = Literal["daily", "weekly"]


class JobAlertSettingsResponse(BaseModel):
    enabled: bool = True
    frequency: JobAlertFrequency = "daily"
    min_fit: float = Field(default=4.0, ge=1.0, le=5.0)
    max_items: int = Field(default=5, ge=1, le=20)
    email_enabled: bool = True
    last_run_at: datetime | None = None


class JobAlertSettingsPatch(BaseModel):
    enabled: bool | None = None
    frequency: JobAlertFrequency | None = None
    min_fit: float | None = Field(default=None, ge=1.0, le=5.0)
    max_items: int | None = Field(default=None, ge=1, le=20)
    email_enabled: bool | None = None


class JobAlertFeedItem(BaseModel):
    delivery_id: str
    delivered_at: datetime
    fit_score: float = Field(ge=1.0, le=5.0)
    job_id: str
    title: str
    company: str
    location: str | None = None
    url: str | None = None
    fit_reasons: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class JobAlertFeedResponse(BaseModel):
    items: list[JobAlertFeedItem]
    total: int
    page: int
    per_page: int
