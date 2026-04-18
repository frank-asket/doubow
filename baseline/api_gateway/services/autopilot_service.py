from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.autopilot_run import AutopilotRun
from schemas.autopilot import AutopilotRunRequest, AutopilotRunResponse
from services.idempotency import payload_fingerprint


async def run_autopilot(
    session: AsyncSession, user_id: str, idempotency_key: str, payload: AutopilotRunRequest
) -> tuple[AutopilotRunResponse, bool]:
    fingerprint = payload_fingerprint(payload.model_dump())
    existing = (
        await session.execute(
            select(AutopilotRun).where(
                AutopilotRun.user_id == user_id,
                AutopilotRun.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()

    if existing:
        if existing.request_fingerprint != fingerprint:
            raise ValueError(existing.id)
        return (
            AutopilotRunResponse(
                run_id=existing.id,
                status="done",
                replayed=True,
                scope=existing.scope,  # type: ignore[arg-type]
                item_results=[],
                started_at=existing.started_at,
                completed_at=existing.completed_at or datetime.now(timezone.utc),
            ),
            True,
        )

    run = AutopilotRun(
        id=str(uuid4()),
        user_id=user_id,
        status="queued",
        scope=payload.scope,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        started_at=datetime.now(timezone.utc),
    )
    session.add(run)
    await session.commit()
    return (
        AutopilotRunResponse(
            run_id=run.id,
            status="queued",
            replayed=False,
            scope=payload.scope,
            item_results=[],
            started_at=run.started_at,
        ),
        False,
    )
