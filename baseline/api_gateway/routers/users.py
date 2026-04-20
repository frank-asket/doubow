from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user, get_current_user_id
from models.user import User
from schemas.dashboard import DashboardSummaryResponse
from schemas.resume import UserPreferencesModel, UserPreferencesPatch
from schemas.users import MeDebugResponse, MeResponse
from services.dashboard_service import get_dashboard_summary as load_dashboard_summary
from services.resume_service import update_preferences_for_user
from services.users_service import user_to_me_response

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=MeResponse)
async def get_me(user: User = Depends(get_authenticated_user)) -> MeResponse:
    return user_to_me_response(user)


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    tags=["dashboard"],
    summary="Dashboard aggregates for badges and Discover stats",
)
async def get_dashboard(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> DashboardSummaryResponse:
    return await load_dashboard_summary(session, user.id)


@router.get("/debug", response_model=MeDebugResponse)
async def get_me_debug(user_id: str = Depends(get_current_user_id)) -> MeDebugResponse:
    return MeDebugResponse(user_id=user_id, auth_source="clerk_jwt")


@router.patch("/preferences", response_model=UserPreferencesModel)
async def patch_preferences(
    patch: UserPreferencesPatch,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> UserPreferencesModel:
    try:
        return await update_preferences_for_user(session, user.id, patch)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found — upload a resume before updating preferences.",
        )
