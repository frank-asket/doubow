from fastapi import APIRouter, Depends

from dependencies import get_authenticated_user, get_current_user_id
from models.user import User
from schemas.users import MeDebugResponse, MeResponse
from services.users_service import user_to_me_response

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=MeResponse)
async def get_me(user: User = Depends(get_authenticated_user)) -> MeResponse:
    return user_to_me_response(user)


@router.get("/debug", response_model=MeDebugResponse)
async def get_me_debug(user_id: str = Depends(get_current_user_id)) -> MeDebugResponse:
    return MeDebugResponse(user_id=user_id, auth_source="clerk_jwt")
