from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.applications import (
    ApplicationsListResponse,
    CreateApplicationRequest,
    IntegrityCheckRequest,
    IntegrityCheckResponse,
    Application,
)
from services.applications_service import create_application, integrity_check, list_applications

router = APIRouter(prefix="/me/applications", tags=["applications"])


@router.get("", response_model=ApplicationsListResponse)
async def list_applications_route(
    status: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ApplicationsListResponse:
    return await list_applications(session=session, user_id=user.id, status=status)


@router.post("", response_model=Application)
async def create_application_route(
    payload: CreateApplicationRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> Application:
    return await create_application(session=session, user_id=user.id, payload=payload)


@router.post("/integrity-check", response_model=IntegrityCheckResponse)
async def integrity_check_route(
    payload: IntegrityCheckRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> IntegrityCheckResponse:
    return await integrity_check(session=session, user_id=user.id, mode=payload.mode)
