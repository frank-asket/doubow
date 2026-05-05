from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from services.approvals_service import (
    ApprovalIdempotencyConflictError,
    approve_approval as approve_approval_service,
    reject_approval as reject_approval_service,
)
from services.send_approval_service import schedule_post_approve_dispatch


@dataclass
class ApprovalActionError(Exception):
    code: str
    detail: str


async def approve_outbound_draft_action(
    *,
    session: AsyncSession,
    user_id: str,
    approval_id: str | None,
) -> str:
    if not approval_id:
        raise ApprovalActionError(
            code="approval_id_required",
            detail="Include an approval id (UUID), e.g. `/approve <uuid>`.",
        )
    try:
        resp = await approve_approval_service(
            session,
            user_id,
            approval_id,
            edited_body=None,
            idempotency_key=f"agent-approve-{uuid4().hex}",
        )
        schedule_post_approve_dispatch(
            approval_id=approval_id,
            user_id=user_id,
            queued_send=bool(resp.queued_send and resp.send_task_id),
            send_task_id=resp.send_task_id,
        )
    except ApprovalIdempotencyConflictError as exc:
        raise ApprovalActionError(
            code="idempotency_conflict",
            detail=f"Approval idempotency conflict with `{exc.prior_approval_id}`.",
        ) from exc
    except ValueError:
        raise ApprovalActionError(
            code="approval_not_found",
            detail=f"Approval `{approval_id}` was not found.",
        ) from None

    return (
        "Summary:\n"
        f"- Approved outbound draft `{approval_id}` (status={resp.status}).\n"
        + (
            "- Outbound send has been queued.\n"
            if resp.queued_send
            else "- No new send was queued (already processed or duplicate approval token).\n"
        )
        + "Recommended Actions:\n"
        "- Track delivery from Approvals / Pipeline.\n"
        "Why:\n"
        "- Approval authorizes the same outbound path as the product UI.\n"
        "Next Step:\n"
        "- Confirm delivery or retry from Approvals if needed."
    )


async def reject_outbound_draft_action(
    *,
    session: AsyncSession,
    user_id: str,
    approval_id: str | None,
) -> str:
    if not approval_id:
        raise ApprovalActionError(
            code="approval_id_required",
            detail="Include an approval id (UUID), e.g. `/reject <uuid>`.",
        )
    try:
        await reject_approval_service(session, user_id, approval_id)
    except ValueError:
        raise ApprovalActionError(
            code="approval_not_found",
            detail=f"Approval `{approval_id}` was not found.",
        ) from None

    return (
        "Summary:\n"
        f"- Rejected and removed pending approval `{approval_id}`.\n"
        "Recommended Actions:\n"
        "- Generate a new draft from Pipeline if you still want to reach out.\n"
        "Why:\n"
        "- Reject removes the draft without sending.\n"
        "Next Step:\n"
        "- Continue reviewing remaining approvals."
    )
