from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.telemetry import (
    ActivationKPIResponse,
    LaunchScorecardResponse,
    OutcomeKPIResponse,
    TelemetryAcknowledgeResponse,
    TelemetryEventIn,
)
from services.telemetry_service import get_activation_kpi, get_launch_scorecard, get_outcome_kpi, record_event

router = APIRouter(prefix="/me/telemetry", tags=["telemetry"])


@router.post("/events", response_model=TelemetryAcknowledgeResponse)
async def post_event(
    payload: TelemetryEventIn,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> TelemetryAcknowledgeResponse:
    await record_event(session=session, user_id=user.id, payload=payload)
    return TelemetryAcknowledgeResponse()


@router.get("/activation-kpi", response_model=ActivationKPIResponse)
async def activation_kpi(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ActivationKPIResponse:
    return await get_activation_kpi(session=session, user_id=user.id)


@router.get("/outcome-kpi", response_model=OutcomeKPIResponse)
async def outcome_kpi(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> OutcomeKPIResponse:
    return await get_outcome_kpi(session=session, user_id=user.id)


@router.get("/launch-scorecard", response_model=LaunchScorecardResponse)
async def launch_scorecard(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> LaunchScorecardResponse:
    return await get_launch_scorecard(session=session, user_id=user.id)
