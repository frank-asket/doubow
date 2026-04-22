from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AutopilotScope = Literal["all", "failed_only", "gmail_failed_only"]
RunStatus = Literal["queued", "running", "done", "failed"]
ItemStatus = Literal["success", "failed", "skipped"]


class AutopilotRunRequest(BaseModel):
    scope: AutopilotScope = Field(
        default="all",
        description=(
            "`all`: up to 100 apps for the user. `failed_only` / `gmail_failed_only`: retry targets "
            "derived from the latest completed autopilot run with item_results."
        ),
    )
    application_ids: list[str] | None = None


class AutopilotRunItem(BaseModel):
    application_id: str
    status: ItemStatus
    retryable: bool
    suggested_action: str | None = None
    latency_ms: int
    error: str | None = None


class AutopilotRunResponse(BaseModel):
    run_id: str
    status: RunStatus
    replayed: bool = False
    scope: AutopilotScope
    item_results: list[AutopilotRunItem] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class IdempotencyConflictResponse(BaseModel):
    error: Literal["idempotency_conflict"] = "idempotency_conflict"
    detail: str
    prior_run_id: str
