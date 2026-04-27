from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval
from models.telemetry_event import TelemetryEvent
from schemas.telemetry import ActivationKPIResponse, OutcomeKPIResponse, TelemetryEventIn
from services.posthog_service import capture_event, fetch_activation_event_pairs


async def record_event(session: AsyncSession, user_id: str, payload: TelemetryEventIn) -> None:
    row = TelemetryEvent(
        user_id=user_id,
        event_name=payload.event_name,
        occurred_at=payload.occurred_at or datetime.now(UTC),
        properties=payload.properties or {},
    )
    session.add(row)
    await session.commit()
    try:
        await capture_event(
            distinct_id=user_id,
            event_name=payload.event_name,
            properties=payload.properties or {},
            occurred_at=payload.occurred_at,
        )
    except Exception:
        # PostHog is best-effort; local telemetry should still succeed.
        return


async def get_activation_kpi(session: AsyncSession, user_id: str) -> ActivationKPIResponse:
    # Prefer PostHog when configured.
    try:
        pairs = await fetch_activation_event_pairs(user_id)
    except Exception:
        pairs = []
    if pairs:
        durations_seconds = [max(0.0, (ready - start).total_seconds()) for start, ready in pairs]
        avg = sum(durations_seconds) / len(durations_seconds)
        return ActivationKPIResponse(
            sample_size=len(durations_seconds),
            latest_time_to_first_matches_seconds=durations_seconds[-1],
            avg_time_to_first_matches_seconds=avg,
        )

    # Fallback to local DB events when PostHog is not configured/reachable.
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


async def get_outcome_kpi(session: AsyncSession, user_id: str) -> OutcomeKPIResponse:
    approvals_created = int(
        (await session.execute(select(func.count()).select_from(Approval).where(Approval.user_id == user_id))).scalar_one()
        or 0
    )

    approvals_resolved = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Approval)
                .where(Approval.user_id == user_id, Approval.status.in_(("approved", "edited", "rejected")))
            )
        ).scalar_one()
        or 0
    )

    approvals_approved_or_edited = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Approval)
                .where(Approval.user_id == user_id, Approval.status.in_(("approved", "edited")))
            )
        ).scalar_one()
        or 0
    )

    approvals_sent = int(
        (
            await session.execute(
                select(func.count()).select_from(Approval).where(Approval.user_id == user_id, Approval.sent_at.is_not(None))
            )
        ).scalar_one()
        or 0
    )

    def _rate(num: int, den: int) -> float | None:
        if den <= 0:
            return None
        return float(num) / float(den)

    return OutcomeKPIResponse(
        approvals_created=approvals_created,
        approvals_resolved=approvals_resolved,
        approvals_approved_or_edited=approvals_approved_or_edited,
        approvals_sent=approvals_sent,
        approval_resolution_rate=_rate(approvals_resolved, approvals_created),
        approval_acceptance_rate=_rate(approvals_approved_or_edited, approvals_created),
        approval_send_rate=_rate(approvals_sent, approvals_created),
    )
