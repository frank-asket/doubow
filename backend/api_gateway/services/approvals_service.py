from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.approval import Approval
from models.job import Job
from models.job_score import JobScore as JobScoreRow
from schemas.approvals import Approval as ApprovalSchema
from schemas.approvals import ApproveApprovalResponse
from services.application_schema import application_to_schema


class ApprovalIdempotencyConflictError(Exception):
    def __init__(self, prior_approval_id: str):
        super().__init__(prior_approval_id)
        self.prior_approval_id = prior_approval_id


def build_approval_schema(
    approval: Approval, app: Application, job: Job, score_row: JobScoreRow | None
) -> ApprovalSchema:
    app_schema = application_to_schema(app, job, score_row, approval=approval)
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
        send_provider=approval.send_provider,
        delivery_status=approval.delivery_status,
        delivery_error=approval.delivery_error,
        provider_message_id=approval.provider_message_id,
        provider_thread_id=approval.provider_thread_id,
        provider_confirmed_at=approval.provider_confirmed_at,
        idempotency_key=approval.idempotency_key or f"approval-{approval.id}",
        created_at=approval.created_at,
    )


async def list_approvals(session: AsyncSession, user_id: str) -> list[ApprovalSchema]:
    stmt = (
        select(Approval, Application, Job, JobScoreRow)
        .join(Application, Application.id == Approval.application_id)
        .join(Job, Job.id == Application.job_id)
        .outerjoin(
            JobScoreRow,
            (JobScoreRow.job_id == Job.id) & (JobScoreRow.user_id == Application.user_id),
        )
        .where(Approval.user_id == user_id)
    )
    rows = (await session.execute(stmt.order_by(Approval.created_at.desc()))).all()
    return [build_approval_schema(approval, app, job, score_row) for approval, app, job, score_row in rows]


async def approve_approval(
    session: AsyncSession, user_id: str, approval_id: str, edited_body: str | None, idempotency_key: str
) -> ApproveApprovalResponse:
    approval = (
        await session.execute(
            select(Approval).where(Approval.id == approval_id, Approval.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not approval:
        raise ValueError("Approval not found")

    if approval.idempotency_key:
        if approval.idempotency_key != idempotency_key:
            raise ApprovalIdempotencyConflictError(approval.id)
        return ApproveApprovalResponse(
            approval_id=approval.id,
            status=approval.status,  # type: ignore[arg-type]
            queued_send=False,
            send_task_id=None,
        )

    approval.idempotency_key = idempotency_key
    if edited_body is not None:
        approval.draft_body = edited_body
        approval.status = "edited"
    else:
        approval.status = "approved"
    approval.delivery_status = "queued"
    approval.delivery_error = None
    approval.send_provider = None
    approval.provider_message_id = None
    approval.provider_thread_id = None
    approval.provider_confirmed_at = None
    approval.sent_at = None
    approval.approved_at = datetime.now(timezone.utc)
    await session.commit()
    return ApproveApprovalResponse(
        approval_id=approval.id,
        status=approval.status,  # type: ignore[arg-type]
        queued_send=True,
        send_task_id=str(uuid4()),
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
