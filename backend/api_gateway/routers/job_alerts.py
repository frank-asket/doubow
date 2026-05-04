from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.job_alerts import JobAlertFeedResponse, JobAlertSettingsPatch, JobAlertSettingsResponse
from services.job_alert_service import get_job_alert_settings, list_job_alert_feed, patch_job_alert_settings

router = APIRouter(prefix="/me/job-alerts", tags=["job-alerts"])


@router.get("/settings", response_model=JobAlertSettingsResponse)
async def get_job_alert_settings_route(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> JobAlertSettingsResponse:
    return await get_job_alert_settings(session=session, user_id=user.id)


@router.put("/settings", response_model=JobAlertSettingsResponse)
async def update_job_alert_settings_route(
    payload: JobAlertSettingsPatch,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> JobAlertSettingsResponse:
    return await patch_job_alert_settings(session=session, user_id=user.id, payload=payload)


@router.get("/feed", response_model=JobAlertFeedResponse)
async def get_job_alert_feed_route(
    page: int = 1,
    per_page: int = 20,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> JobAlertFeedResponse:
    return await list_job_alert_feed(session=session, user_id=user.id, page=page, per_page=per_page)
