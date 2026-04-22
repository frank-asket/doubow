from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.autopilot_run import AutopilotRun
from schemas.autopilot import AutopilotRunRequest, AutopilotRunResponse
from services.autopilot_response import autopilot_run_to_response
from services.idempotency import payload_fingerprint


async def get_autopilot_run(session: AsyncSession, user_id: str, run_id: str) -> AutopilotRunResponse | None:
    row = await session.get(AutopilotRun, run_id)
    if row is None or row.user_id != user_id:
        return None
    return autopilot_run_to_response(row, replayed=False)


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
        return (autopilot_run_to_response(existing, replayed=True), True)

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
    return (autopilot_run_to_response(run, replayed=False), False)


async def list_autopilot_runs(
    session: AsyncSession, user_id: str, limit: int = 20
) -> list[AutopilotRunResponse]:
    rows = (
        await session.execute(
            select(AutopilotRun)
            .where(AutopilotRun.user_id == user_id)
            .order_by(AutopilotRun.created_at.desc())
            .limit(limit)
        )
    ).scalars()
    return [autopilot_run_to_response(row, replayed=False) for row in rows]
