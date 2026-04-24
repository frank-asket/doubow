from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user, require_idempotency_key
from models.user import User
from schemas.autopilot import (
    AutopilotRunRequest,
    AutopilotRunResponse,
    AutopilotResumeResponse,
    IdempotencyConflictResponse,
)
from services.autopilot_resume import release_resume_slot, try_acquire_resume_slot, validate_resume_eligibility
from services.autopilot_runner import execute_autopilot_run_background
from services.autopilot_service import (
    get_autopilot_run as get_autopilot_run_service,
    list_autopilot_runs as list_autopilot_runs_service,
    run_autopilot as run_autopilot_service,
)

router = APIRouter(prefix="/me/autopilot", tags=["autopilot"])


async def _execute_autopilot_resume_task(
    run_id: str,
    user_id: str,
    application_ids: list[str] | None,
) -> None:
    try:
        await execute_autopilot_run_background(run_id, user_id, application_ids)
    finally:
        release_resume_slot(run_id)


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


@router.post(
    "/runs/{run_id}/resume",
    response_model=AutopilotResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def resume_autopilot_run_route(
    run_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> AutopilotResumeResponse:
    """Re-enqueue execution for a **running** autopilot run (e.g. worker crashed after checkpoint).

    Requires a stored LangGraph checkpoint when checkpointing is enabled.
    """
    _, reason = await validate_resume_eligibility(session=session, user_id=user.id, run_id=run_id)
    if reason:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=reason)

    acquired = await try_acquire_resume_slot(run_id)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resume already in progress for this run",
        )

    background_tasks.add_task(
        _execute_autopilot_resume_task,
        run_id,
        user.id,
        None,
    )
    return AutopilotResumeResponse(run_id=run_id, enqueued=True, detail=None)


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
