from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from dependencies import require_idempotency_key
from schemas.autopilot import (
    AutopilotRunRequest,
    AutopilotRunResponse,
    IdempotencyConflictResponse,
)
from services.idempotency import get_record, payload_fingerprint, save_record

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
) -> AutopilotRunResponse:
    payload_data = payload.model_dump()
    prior = get_record(idempotency_key)
    current_fingerprint = payload_fingerprint(payload_data)

    if prior:
        if prior.payload_fingerprint != current_fingerprint:
            body = IdempotencyConflictResponse(
                detail="Key already used with a different payload fingerprint",
                prior_run_id=prior.run_id,
            )
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump())
        return AutopilotRunResponse(
            run_id=prior.run_id,
            status="done",
            replayed=True,
            scope=payload.scope,
            item_results=[],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

    run_id = str(uuid4())
    save_record(idempotency_key, run_id=run_id, payload=payload_data)
    return AutopilotRunResponse(
        run_id=run_id,
        status="queued",
        replayed=False,
        scope=payload.scope,
        item_results=[],
        started_at=datetime.now(timezone.utc),
    )
