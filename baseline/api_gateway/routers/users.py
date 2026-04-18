from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_current_user_claims, get_current_user_id
from schemas.users import MeDebugResponse, MeResponse
from services.users_service import get_me as get_me_service

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=MeResponse)
async def get_me(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    claims: dict = Depends(get_current_user_claims),
) -> MeResponse:
    return await get_me_service(session=session, user_id=user_id, claims=claims)


@router.get("/debug", response_model=MeDebugResponse)
async def get_me_debug(user_id: str = Depends(get_current_user_id)) -> MeDebugResponse:
    return MeDebugResponse(user_id=user_id, auth_source="clerk_jwt")
