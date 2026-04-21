from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.telemetry import ActivationKPIResponse, TelemetryAcknowledgeResponse, TelemetryEventIn
from services.telemetry_service import get_activation_kpi, record_event

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
