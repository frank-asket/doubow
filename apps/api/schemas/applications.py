from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from schemas.jobs import Job, JobScore

ApplicationStatus = Literal["saved", "pending", "applied", "interview", "offer", "rejected"]
IntegrityMode = Literal["dry_run", "apply"]
IntegrityChangeType = Literal["deduplicate", "mark_stale", "normalize_status"]
Channel = Literal["email", "linkedin", "company_site"]


class Application(BaseModel):
    id: str
    user_id: str
    job: Job
    score: JobScore | None = None
    status: ApplicationStatus
    channel: Channel
    applied_at: datetime | None = None
    last_updated: datetime
    idempotency_key: str | None = None
    notes: str | None = None
    is_stale: bool = False
    dedup_group: str | None = None


class ApplicationsListResponse(BaseModel):
    items: list[Application]
    total: int
    page: int
    per_page: int


class CreateApplicationRequest(BaseModel):
    job_id: str
    channel: Channel


class IntegrityCheckRequest(BaseModel):
    mode: IntegrityMode


class IntegritySummary(BaseModel):
    duplicates: int
    stale: int
    status_fixes: int


class IntegrityChange(BaseModel):
    type: IntegrityChangeType
    application_ids: list[str]
    keep_id: str | None = None
    reason: str


class IntegrityCheckResponse(BaseModel):
    mode: IntegrityMode
    summary: IntegritySummary
    changes: list[IntegrityChange]
