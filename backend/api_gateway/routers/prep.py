from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.errors import ErrorResponse
from schemas.prep import PrepAssistRequest, PrepAssistResponse, PrepGenerateRequest, PrepSessionDetailResponse
from services.prep_assist_service import generate_prep_assist_text
from services.prep_service import PrepApplicationNotFoundError, generate_prep_for_application, get_prep_detail_for_user

router = APIRouter(prefix="/me/prep", tags=["prep"])


@router.get("", response_model=PrepSessionDetailResponse)
async def get_prep_route(
    application_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> PrepSessionDetailResponse:
    res = await get_prep_detail_for_user(session, user.id, application_id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prep session not found")
    return res


@router.post(
    "/generate",
    response_model=PrepSessionDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
async def generate_prep_route(
    payload: PrepGenerateRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> PrepSessionDetailResponse:
    try:
        return await generate_prep_for_application(session, user.id, payload.application_id)
    except PrepApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/assist",
    response_model=PrepAssistResponse,
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def prep_assist_route(
    payload: PrepAssistRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> PrepAssistResponse:
    try:
        text = await generate_prep_assist_text(session, user.id, payload.application_id, payload.kind)
    except PrepApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return PrepAssistResponse(text=text)
