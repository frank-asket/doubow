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
    "pricing_interval_toggled",
    "pricing_cta_clicked",
    "pricing_billing_link_clicked",
    "onboarding_step_clicked",
    "onboarding_skip_clicked",
    "settings_reconnect_clicked",
    "settings_contact_support_clicked",
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


class OutcomeKPIResponse(BaseModel):
    approvals_created: int
    approvals_resolved: int
    approvals_approved_or_edited: int
    approvals_sent: int
    approval_resolution_rate: float | None = None
    approval_acceptance_rate: float | None = None
    approval_send_rate: float | None = None


class StabilityKPIResponse(BaseModel):
    window_days: int = 7
    autopilot_runs_total: int
    autopilot_runs_failed: int
    autopilot_runs_running: int
    approvals_pending: int
    approvals_delivery_failed: int
    approval_delivery_failure_rate: float | None = None


class LaunchScorecardResponse(BaseModel):
    generated_at: datetime
    signal: Literal["go", "watch", "no_go"]
    reasons: list[str] = Field(default_factory=list)
    activation: ActivationKPIResponse
    outcome: OutcomeKPIResponse
    stability: StabilityKPIResponse
