from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from config import settings
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from dependencies import require_idempotency_key
from schemas.errors import ErrorResponse
from schemas.approvals import (
    Approval,
    ApprovalIdempotencyConflictResponse,
    ApproveApprovalRequest,
    ApproveApprovalResponse,
)
from services.approvals_service import (
    ApprovalIdempotencyConflictError,
    approve_approval as approve_approval_service,
    list_approvals as list_approvals_service,
    reject_approval as reject_approval_service,
)
from services.send_approval_service import run_send_stub_in_background

router = APIRouter(prefix="/me/approvals", tags=["approvals"])


@router.get("", response_model=list[Approval])
async def list_approvals_route(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> list[Approval]:
    return await list_approvals_service(session=session, user_id=user.id)


@router.post(
    "/{approval_id}/approve",
    response_model=ApproveApprovalResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ApprovalIdempotencyConflictResponse}},
)
async def approve_approval(
    approval_id: str,
    payload: ApproveApprovalRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str = Depends(require_idempotency_key),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ApproveApprovalResponse:
    try:
        response = await approve_approval_service(
            session=session,
            user_id=user.id,
            approval_id=approval_id,
            edited_body=payload.edited_body,
            idempotency_key=idempotency_key,
        )
        if response.queued_send and response.send_task_id:
            if settings.use_celery_for_send:
                try:
                    from tasks.send_tasks import send_approval_stub_task

                    send_approval_stub_task.delay(approval_id, user.id)
                except Exception:
                    background_tasks.add_task(run_send_stub_in_background, approval_id, user.id)
            else:
                background_tasks.add_task(run_send_stub_in_background, approval_id, user.id)
        return response
    except ApprovalIdempotencyConflictError as exc:
        body = ApprovalIdempotencyConflictResponse(
            detail="Key already used with a different approval submission",
            prior_approval_id=exc.prior_approval_id,
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{approval_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def reject_approval_route(
    approval_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> None:
    try:
        await reject_approval_service(session=session, user_id=user.id, approval_id=approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
