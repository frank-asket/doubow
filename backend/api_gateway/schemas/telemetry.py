from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TelemetryEventName = Literal[
    "discover_empty_viewed",
    "resume_upload_started",
    "resume_upload_succeeded",
    "match_scoring_started",
    "match_scoring_eta_shown",
    "first_matches_ready",
]


class TelemetryEventIn(BaseModel):
    event_name: TelemetryEventName
    occurred_at: datetime | None = None
    properties: dict = Field(default_factory=dict)


class TelemetryAcknowledgeResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ActivationKPIResponse(BaseModel):
    sample_size: int
    latest_time_to_first_matches_seconds: float | None = None
    avg_time_to_first_matches_seconds: float | None = None
