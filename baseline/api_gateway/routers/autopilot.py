from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_current_user_id
from dependencies import require_idempotency_key
from schemas.autopilot import (
    AutopilotRunRequest,
    AutopilotRunResponse,
    IdempotencyConflictResponse,
)
from services.autopilot_service import run_autopilot as run_autopilot_service

router = APIRouter(prefix="/me/autopilot", tags=["autopilot"])


@router.post(
    "/run",
    response_model=AutopilotRunResponse,
    responses={409: {"model": IdempotencyConflictResponse}},
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_autopilot(
    payload: AutopilotRunRequest,
    idempotency_key: str = Depends(require_idempotency_key),
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> AutopilotRunResponse:
    try:
        response, replayed = await run_autopilot_service(
            session=session,
            user_id=user_id,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        if replayed:
            return response
        return response
    except ValueError as exc:
        body = IdempotencyConflictResponse(
            detail="Key already used with a different payload fingerprint",
            prior_run_id=str(exc),
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump())
