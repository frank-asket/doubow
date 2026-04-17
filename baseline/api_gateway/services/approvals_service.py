from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.approval import Approval
from models.job import Job
from schemas.approvals import Approval as ApprovalSchema
from schemas.approvals import ApproveApprovalResponse
from schemas.applications import Application as ApplicationSchema
from schemas.jobs import DimensionScores, Job as JobSchema, JobScore


def _approval_to_schema(approval: Approval, app: Application, job: Job) -> ApprovalSchema:
    now = datetime.now(timezone.utc)
    app_schema = ApplicationSchema(
        id=app.id,
        user_id=app.user_id,
        job=JobSchema(
            id=job.id,
            source=job.source,
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            location=job.location or "Remote",
            salary_range=job.salary_range,
            description=job.description or "",
            url=job.url or "",
            posted_at=job.posted_at,
            discovered_at=job.discovered_at,
        ),
        score=JobScore(
            job_id=job.id,
            fit_score=4.2,
            fit_reasons=["Profile and role share relevant stack"],
            risk_flags=[],
            dimension_scores=DimensionScores(tech=4.2, culture=4.0, seniority=4.3, comp=4.1, location=4.4),
            channel_recommendation=app.channel,
            scored_at=now,
        ),
        status=app.status,
        channel=app.channel,
        applied_at=app.applied_at,
        last_updated=app.last_updated,
        idempotency_key=app.idempotency_key,
        notes=app.notes,
        is_stale=app.is_stale,
        dedup_group=app.dedup_group,
    )
    return ApprovalSchema(
        id=approval.id,
        application=app_schema,
        type=approval.type,
        channel=approval.channel,
        subject=approval.subject,
        draft_body=approval.draft_body,
        status=approval.status,
        approved_at=approval.approved_at,
        sent_at=approval.sent_at,
        idempotency_key=approval.idempotency_key or f"approval-{approval.id}",
        created_at=approval.created_at,
    )


async def list_approvals(session: AsyncSession, user_id: str) -> list[ApprovalSchema]:
    stmt = (
        select(Approval, Application, Job)
        .join(Application, Application.id == Approval.application_id)
        .join(Job, Job.id == Application.job_id)
        .where(Approval.user_id == user_id)
    )
    rows = (await session.execute(stmt.order_by(Approval.created_at.desc()))).all()
    return [_approval_to_schema(approval, app, job) for approval, app, job in rows]


async def approve_approval(
    session: AsyncSession, user_id: str, approval_id: str, edited_body: str | None
) -> ApproveApprovalResponse:
    approval = (
        await session.execute(
            select(Approval).where(Approval.id == approval_id, Approval.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not approval:
        raise ValueError("Approval not found")
    if edited_body is not None:
        approval.draft_body = edited_body
        approval.status = "edited"
    approval.status = "approved"
    approval.approved_at = datetime.now(timezone.utc)
    await session.commit()
    return ApproveApprovalResponse(
        approval_id=approval.id,
        status=approval.status,
        queued_send=True,
        send_task_id=f"send_{uuid4().hex[:10]}",
    )


async def reject_approval(session: AsyncSession, user_id: str, approval_id: str) -> None:
    approval = (
        await session.execute(
            select(Approval).where(Approval.id == approval_id, Approval.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not approval:
        raise ValueError("Approval not found")
    await session.delete(approval)
    await session.commit()
