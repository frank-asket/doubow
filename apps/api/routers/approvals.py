from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_current_user_id
from dependencies import require_idempotency_key
from schemas.approvals import Approval, ApproveApprovalRequest, ApproveApprovalResponse
from services.approvals_service import (
    approve_approval as approve_approval_service,
    list_approvals as list_approvals_service,
    reject_approval as reject_approval_service,
)

router = APIRouter(prefix="/me/approvals", tags=["approvals"])


@router.get("", response_model=list[Approval])
async def list_approvals_route(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> list[Approval]:
    return await list_approvals_service(session=session, user_id=user_id)


@router.post("/{approval_id}/approve", response_model=ApproveApprovalResponse)
async def approve_approval(
    approval_id: str,
    payload: ApproveApprovalRequest,
    _: str = Depends(require_idempotency_key),
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> ApproveApprovalResponse:
    try:
        return await approve_approval_service(
            session=session,
            user_id=user_id,
            approval_id=approval_id,
            edited_body=payload.edited_body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{approval_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_approval_route(
    approval_id: str,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> None:
    try:
        await reject_approval_service(session=session, user_id=user_id, approval_id=approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
