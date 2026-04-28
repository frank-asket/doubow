from datetime import datetime, timezone
from uuid import uuid4
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.approval import Approval
from models.job import Job
from models.job_score import JobScore as JobScoreRow
from schemas.approvals import Approval as ApprovalSchema
from schemas.approvals import ApproveApprovalResponse
from services.application_schema import application_to_schema

_ALLOWED_APPROVAL_TYPES = {"cover_letter", "linkedin_note", "follow_up"}
_ALLOWED_APPROVAL_STATUSES = {"pending", "approved", "rejected", "edited"}
_ALLOWED_DELIVERY_STATUSES = {
    "not_sent",
    "queued",
    "draft_created",
    "provider_accepted",
    "provider_confirmed",
    "failed",
}
_ALLOWED_CHANNELS = {"email", "linkedin", "company_site"}
_ALLOWED_CONFIRMATION_COPY_STATUSES = {"pending", "delivered", "failed", "not_applicable"}
logger = logging.getLogger(__name__)


def _safe_approval_type(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_APPROVAL_TYPES else "cover_letter"


def _safe_approval_status(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_APPROVAL_STATUSES else "pending"


def _safe_delivery_status(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_DELIVERY_STATUSES else "not_sent"


def _safe_channel(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_CHANNELS else "email"


def _confirmation_copy_status(approval: Approval) -> str:
    if _safe_channel(approval.channel) != "email":
        return "not_applicable"
    err = str(approval.delivery_error or "").lower()
    if "confirmation_copy_failed" in err:
        return "failed"
    status = _safe_delivery_status(approval.delivery_status)
    if status in {"provider_accepted", "provider_confirmed", "draft_created"}:
        return "delivered"
    return "pending"


class ApprovalIdempotencyConflictError(Exception):
    def __init__(self, prior_approval_id: str):
        super().__init__(prior_approval_id)
        self.prior_approval_id = prior_approval_id


def build_approval_schema(
    approval: Approval, app: Application, job: Job, score_row: JobScoreRow | None
) -> ApprovalSchema:
    app_schema = application_to_schema(app, job, score_row, approval=approval)
    confirmation_copy_status = _confirmation_copy_status(approval)
    return ApprovalSchema(
        id=approval.id,
        application=app_schema,
        type=_safe_approval_type(approval.type),  # type: ignore[arg-type]
        channel=_safe_channel(approval.channel),  # type: ignore[arg-type]
        subject=approval.subject,
        draft_body=approval.draft_body,
        status=_safe_approval_status(approval.status),  # type: ignore[arg-type]
        approved_at=approval.approved_at,
        sent_at=approval.sent_at,
        send_provider=approval.send_provider,
        delivery_status=_safe_delivery_status(approval.delivery_status),  # type: ignore[arg-type]
        delivery_error=approval.delivery_error,
        provider_message_id=approval.provider_message_id,
        provider_thread_id=approval.provider_thread_id,
        provider_confirmed_at=approval.provider_confirmed_at,
        confirmation_copy_status=(
            confirmation_copy_status if confirmation_copy_status in _ALLOWED_CONFIRMATION_COPY_STATUSES else "pending"
        ),  # type: ignore[arg-type]
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
    items: list[ApprovalSchema] = []
    for approval, app, job, score_row in rows:
        try:
            items.append(build_approval_schema(approval, app, job, score_row))
        except Exception:
            # Keep endpoint available even if one historical approval row is malformed.
            logger.exception("Skipping malformed approval payload user=%s approval=%s", user_id, approval.id)
    return items


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
