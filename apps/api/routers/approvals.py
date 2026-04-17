from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import require_idempotency_key
from schemas.approvals import Approval, ApproveApprovalRequest, ApproveApprovalResponse
from schemas.applications import Application
from schemas.jobs import DimensionScores, Job, JobScore

router = APIRouter(prefix="/me/approvals", tags=["approvals"])

NOW = datetime.now(timezone.utc)
_JOB = Job(
    id="job_001",
    source="greenhouse",
    external_id="gh_001",
    title="Senior ML Engineer",
    company="Mistral AI",
    location="Remote · Paris",
    salary_range="EUR130k-EUR160k",
    description="Build production RAG and agentic systems.",
    url="https://example.com/jobs/job_001",
    posted_at=NOW,
    discovered_at=NOW,
)
_SCORE = JobScore(
    job_id="job_001",
    fit_score=4.8,
    fit_reasons=["Strong RAG match"],
    risk_flags=[],
    dimension_scores=DimensionScores(tech=4.9, culture=4.5, seniority=4.9, comp=4.7, location=5.0),
    channel_recommendation="email",
    scored_at=NOW,
)
_APP = Application(
    id="app_001",
    user_id="dev-user",
    job=_JOB,
    score=_SCORE,
    status="pending",
    channel="email",
    last_updated=NOW,
    is_stale=False,
)
APPROVALS: list[Approval] = [
    Approval(
        id="appr_001",
        application=_APP,
        type="cover_letter",
        channel="email",
        subject="Application: Senior ML Engineer",
        draft_body="Dear Hiring Team,\n\nI am excited to apply for the Senior ML Engineer role at Mistral AI...",
        status="pending",
        idempotency_key="approval-appr_001",
        created_at=NOW,
    )
]


@router.get("", response_model=list[Approval])
async def list_approvals() -> list[Approval]:
    return APPROVALS


@router.post("/{approval_id}/approve", response_model=ApproveApprovalResponse)
async def approve_approval(
    approval_id: str,
    payload: ApproveApprovalRequest,
    _: str = Depends(require_idempotency_key),
) -> ApproveApprovalResponse:
    approval = next((a for a in APPROVALS if a.id == approval_id), None)
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

    if payload.edited_body is not None:
        approval.draft_body = payload.edited_body
        approval.status = "edited"

    approval.status = "approved"
    approval.approved_at = datetime.now(timezone.utc)
    return ApproveApprovalResponse(
        approval_id=approval.id,
        status=approval.status,
        queued_send=True,
        send_task_id=f"send_{uuid4().hex[:10]}",
    )


@router.post("/{approval_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_approval(approval_id: str) -> None:
    index = next((i for i, a in enumerate(APPROVALS) if a.id == approval_id), None)
    if index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    APPROVALS.pop(index)
