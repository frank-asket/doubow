from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.telemetry_event import TelemetryEvent
from schemas.telemetry import ActivationKPIResponse, TelemetryEventIn


async def record_event(session: AsyncSession, user_id: str, payload: TelemetryEventIn) -> None:
    row = TelemetryEvent(
        user_id=user_id,
        event_name=payload.event_name,
        occurred_at=payload.occurred_at or datetime.now(UTC),
        properties=payload.properties or {},
    )
    session.add(row)
    await session.commit()


async def get_activation_kpi(session: AsyncSession, user_id: str) -> ActivationKPIResponse:
    stmt = (
        select(TelemetryEvent)
        .where(
            TelemetryEvent.user_id == user_id,
            TelemetryEvent.event_name.in_(("resume_upload_succeeded", "first_matches_ready")),
        )
        .order_by(TelemetryEvent.occurred_at.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()

    upload_times: list[datetime] = []
    durations_seconds: list[float] = []
    for row in rows:
        if row.event_name == "resume_upload_succeeded":
            upload_times.append(row.occurred_at)
            continue
        if row.event_name == "first_matches_ready" and upload_times:
            start = upload_times.pop(0)
            durations_seconds.append(max(0.0, (row.occurred_at - start).total_seconds()))

    if not durations_seconds:
        return ActivationKPIResponse(sample_size=0)

    avg = sum(durations_seconds) / len(durations_seconds)
    return ActivationKPIResponse(
        sample_size=len(durations_seconds),
        latest_time_to_first_matches_seconds=durations_seconds[-1],
        avg_time_to_first_matches_seconds=avg,
    )
