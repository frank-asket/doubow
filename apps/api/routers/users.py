from fastapi import APIRouter
from schemas.users import MeResponse
from services.users_service import get_me as get_me_service

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=MeResponse)
async def get_me() -> MeResponse:
    return await get_me_service()
