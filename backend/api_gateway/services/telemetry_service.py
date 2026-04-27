from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval
from models.autopilot_run import AutopilotRun
from models.telemetry_event import TelemetryEvent
from schemas.telemetry import (
    ActivationKPIResponse,
    LaunchScorecardResponse,
    OutcomeKPIResponse,
    StabilityKPIResponse,
    TelemetryEventIn,
)
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


async def get_stability_kpi(session: AsyncSession, user_id: str, *, window_days: int = 7) -> StabilityKPIResponse:
    cutoff = datetime.now(UTC) - timedelta(days=max(1, window_days))

    autopilot_runs_total = int(
        (
            await session.execute(
                select(func.count())
                .select_from(AutopilotRun)
                .where(AutopilotRun.user_id == user_id, AutopilotRun.created_at >= cutoff)
            )
        ).scalar_one()
        or 0
    )
    autopilot_runs_failed = int(
        (
            await session.execute(
                select(func.count())
                .select_from(AutopilotRun)
                .where(
                    AutopilotRun.user_id == user_id,
                    AutopilotRun.created_at >= cutoff,
                    AutopilotRun.status == "failed",
                )
            )
        ).scalar_one()
        or 0
    )
    autopilot_runs_running = int(
        (
            await session.execute(
                select(func.count())
                .select_from(AutopilotRun)
                .where(
                    AutopilotRun.user_id == user_id,
                    AutopilotRun.created_at >= cutoff,
                    AutopilotRun.status == "running",
                )
            )
        ).scalar_one()
        or 0
    )

    approvals_pending = int(
        (
            await session.execute(
                select(func.count()).select_from(Approval).where(Approval.user_id == user_id, Approval.status == "pending")
            )
        ).scalar_one()
        or 0
    )
    approvals_delivery_failed = int(
        (
            await session.execute(
                select(func.count()).select_from(Approval).where(
                    Approval.user_id == user_id,
                    (
                        Approval.delivery_error.is_not(None)
                        | Approval.delivery_status.in_(("failed", "error", "provider_failed"))
                    ),
                )
            )
        ).scalar_one()
        or 0
    )

    delivery_failure_rate = None
    if approvals_pending + approvals_delivery_failed > 0:
        delivery_failure_rate = float(approvals_delivery_failed) / float(approvals_pending + approvals_delivery_failed)

    return StabilityKPIResponse(
        window_days=max(1, window_days),
        autopilot_runs_total=autopilot_runs_total,
        autopilot_runs_failed=autopilot_runs_failed,
        autopilot_runs_running=autopilot_runs_running,
        approvals_pending=approvals_pending,
        approvals_delivery_failed=approvals_delivery_failed,
        approval_delivery_failure_rate=delivery_failure_rate,
    )


def _launch_signal(
    *,
    activation: ActivationKPIResponse,
    outcome: OutcomeKPIResponse,
    stability: StabilityKPIResponse,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    signal = "go"

    if stability.autopilot_runs_failed >= 3:
        signal = "no_go"
        reasons.append("autopilot failures are elevated in the last window")
    if (stability.approval_delivery_failure_rate or 0.0) >= 0.15:
        signal = "no_go"
        reasons.append("approval delivery failure rate exceeds 15%")

    if signal != "no_go":
        if stability.autopilot_runs_running >= 5:
            signal = "watch"
            reasons.append("many autopilot runs are still in running state")
        if outcome.approvals_created >= 5 and (outcome.approval_acceptance_rate or 0.0) < 0.2:
            signal = "watch"
            reasons.append("approval acceptance rate is below 20%")
        if activation.sample_size > 0 and (activation.avg_time_to_first_matches_seconds or 0.0) > 24 * 3600:
            signal = "watch"
            reasons.append("activation speed is slower than 24 hours")

    if not reasons:
        reasons.append("core activation, outcome, and stability indicators are within target bounds")
    return signal, reasons


async def get_launch_scorecard(session: AsyncSession, user_id: str) -> LaunchScorecardResponse:
    activation = await get_activation_kpi(session=session, user_id=user_id)
    outcome = await get_outcome_kpi(session=session, user_id=user_id)
    stability = await get_stability_kpi(session=session, user_id=user_id)
    signal, reasons = _launch_signal(activation=activation, outcome=outcome, stability=stability)
    return LaunchScorecardResponse(
        generated_at=datetime.now(UTC),
        signal=signal,
        reasons=reasons,
        activation=activation,
        outcome=outcome,
        stability=stability,
    )
