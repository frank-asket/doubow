from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user, require_idempotency_key
from models.user import User
from schemas.autopilot import (
    AutopilotRunRequest,
    AutopilotRunResponse,
    IdempotencyConflictResponse,
)
from services.autopilot_runner import execute_autopilot_run_background
from services.autopilot_service import (
    get_autopilot_run as get_autopilot_run_service,
    list_autopilot_runs as list_autopilot_runs_service,
    run_autopilot as run_autopilot_service,
)

router = APIRouter(prefix="/me/autopilot", tags=["autopilot"])


@router.post(
    "/run",
    response_model=AutopilotRunResponse,
    responses={409: {"model": IdempotencyConflictResponse}},
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_autopilot_route(
    payload: AutopilotRunRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str = Depends(require_idempotency_key),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> AutopilotRunResponse:
    try:
        response, replayed = await run_autopilot_service(
            session=session,
            user_id=user.id,
            idempotency_key=idempotency_key,
            payload=payload,
        )
        if not replayed and response.status == "queued":
            background_tasks.add_task(
                execute_autopilot_run_background,
                response.run_id,
                user.id,
                payload.application_ids,
            )
        return response
    except ValueError as exc:
        body = IdempotencyConflictResponse(
            detail="Key already used with a different payload fingerprint",
            prior_run_id=str(exc),
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump())


@router.get("/runs/{run_id}", response_model=AutopilotRunResponse)
async def get_autopilot_run_route(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> AutopilotRunResponse:
    row = await get_autopilot_run_service(session, user.id, run_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return row


@router.get("/runs", response_model=list[AutopilotRunResponse])
async def list_autopilot_runs_route(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> list[AutopilotRunResponse]:
    return await list_autopilot_runs_service(session=session, user_id=user.id, limit=max(1, min(limit, 100)))
