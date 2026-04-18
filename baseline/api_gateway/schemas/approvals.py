from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from schemas.applications import Application

ApprovalType = Literal["cover_letter", "linkedin_note", "follow_up"]
ApprovalStatus = Literal["pending", "approved", "rejected", "edited"]
Channel = Literal["email", "linkedin", "company_site"]


class Approval(BaseModel):
    id: str
    application: Application
    type: ApprovalType
    channel: Channel
    subject: str | None = None
    draft_body: str
    status: ApprovalStatus
    approved_at: datetime | None = None
    sent_at: datetime | None = None
    idempotency_key: str
    created_at: datetime


class ApproveApprovalRequest(BaseModel):
    edited_body: str | None = None


class ApproveApprovalResponse(BaseModel):
    approval_id: str
    status: ApprovalStatus
    queued_send: bool
    send_task_id: str | None = None


class ApprovalIdempotencyConflictResponse(BaseModel):
    error: Literal["idempotency_conflict"] = "idempotency_conflict"
    detail: str
    prior_approval_id: str
