from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user, optional_idempotency_key
from models.user import User
from schemas.errors import ErrorResponse
from schemas.applications import (
    Application,
    ApplicationIdempotencyConflictResponse,
    ApplicationsListResponse,
    CreateApplicationRequest,
    IntegrityCheckRequest,
    IntegrityCheckResponse,
)
from schemas.approvals import Approval as ApprovalPayload
from services.applications_service import (
    ApplicationIdempotencyConflictError,
    ApplicationJobNotFoundError,
    create_application,
    integrity_check,
    list_applications,
)
from services.draft_service import ApplicationNotFoundError, create_draft_approval_for_application

router = APIRouter(prefix="/me/applications", tags=["applications"])


@router.get("", response_model=ApplicationsListResponse)
async def list_applications_route(
    status: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ApplicationsListResponse:
    return await list_applications(session=session, user_id=user.id, status=status)


@router.post(
    "",
    response_model=Application,
    responses={404: {"model": ErrorResponse}, 409: {"model": ApplicationIdempotencyConflictResponse}},
)
async def create_application_route(
    payload: CreateApplicationRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
    idempotency_key: str | None = Depends(optional_idempotency_key),
) -> Application | JSONResponse:
    try:
        return await create_application(
            session=session,
            user_id=user.id,
            payload=payload,
            idempotency_key=idempotency_key,
        )
    except ApplicationIdempotencyConflictError as exc:
        body = ApplicationIdempotencyConflictResponse(
            detail="Key already used for a different application payload",
            prior_application_id=exc.prior_application_id,
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump())
    except ApplicationJobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{application_id}/draft",
    response_model=ApprovalPayload,
    responses={404: {"model": ErrorResponse}},
)
async def create_application_draft_route(
    application_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ApprovalPayload:
    try:
        return await create_draft_approval_for_application(session, user.id, application_id)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/integrity-check", response_model=IntegrityCheckResponse)
async def integrity_check_route(
    payload: IntegrityCheckRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> IntegrityCheckResponse:
    return await integrity_check(session=session, user_id=user.id, mode=payload.mode)