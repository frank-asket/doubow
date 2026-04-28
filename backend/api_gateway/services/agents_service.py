from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval
from models.application import Application
from models.autopilot_run import AutopilotRun
from models.job import Job
from models.job_score import JobScore
from schemas.agents import AgentStatusResponse


def _autopilot_run_progress(runs: list[AutopilotRun]) -> float | None:
    """Derive 0–1 progress from persisted autopilot rows (item_results when present, else running/queued mix)."""
    if not runs:
        return None
    item_fractions: list[float] = []
    for run in runs:
        items = run.item_results
        if isinstance(items, list) and len(items) > 0:
            ok = sum(
                1
                for x in items
                if isinstance(x, dict) and str(x.get("status", "")).lower() in ("success", "skipped")
            )
            item_fractions.append(ok / len(items))
    if item_fractions:
        return sum(item_fractions) / len(item_fractions)
    running_ct = sum(1 for r in runs if r.status == "running")
    return running_ct / len(runs)


async def list_agent_status(session: AsyncSession, user_id: str) -> list[AgentStatusResponse]:
    total_jobs = (
        await session.execute(select(func.count(JobScore.id)).where(JobScore.user_id == user_id))
    ).scalar_one()
    pending_approvals = (
        await session.execute(
            select(func.count(Approval.id)).where(Approval.user_id == user_id, Approval.status == "pending")
        )
    ).scalar_one()
    total_approvals = (
        await session.execute(select(func.count(Approval.id)).where(Approval.user_id == user_id))
    ).scalar_one()

    active_run_rows = (
        await session.execute(
            select(AutopilotRun).where(
                AutopilotRun.user_id == user_id,
                AutopilotRun.status.in_(["queued", "running"]),
            )
        )
    ).scalars().all()
    active_runs = list(active_run_rows)
    active_run_count = len(active_runs)

    latest_run = (
        await session.execute(
            select(AutopilotRun)
            .where(AutopilotRun.user_id == user_id)
            .order_by(AutopilotRun.started_at.desc().nulls_last(), AutopilotRun.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    latest_run_iso = None
    if latest_run is not None and latest_run.started_at is not None:
        latest_run_iso = latest_run.started_at.isoformat()

    scorer_progress: float | None = None
    if active_run_count > 0:
        scorer_progress = _autopilot_run_progress(active_runs)

    orch_progress: float | None = None
    if total_approvals > 0:
        orch_progress = (total_approvals - pending_approvals) / total_approvals

    scorer_status = "running" if active_run_count > 0 else "idle"
    scorer_message = "Scoring active pipeline" if active_run_count > 0 else "Waiting for new runs"
    if latest_run is not None and latest_run.status == "failed":
        scorer_status = "error"
        scorer_message = latest_run.failure_detail or "Latest scoring run failed"

    orchestrator_status = "running" if pending_approvals > 0 else "idle"
    orchestrator_message = f"{pending_approvals} approvals awaiting action"
    if latest_run is not None and latest_run.status == "failed" and pending_approvals == 0:
        orchestrator_status = "error"
        orchestrator_message = latest_run.failure_detail or "Latest orchestration run failed"

    return [
        AgentStatusResponse(
            name="discovery",
            label="Discovery agent",
            description="Scans job boards and ATS portals",
            status="active" if total_jobs > 0 else "idle",
            message=f"{total_jobs} indexed jobs",
            items_processed=int(total_jobs),
            last_run=latest_run_iso,
        ),
        AgentStatusResponse(
            name="scorer",
            label="Match scorer",
            description="Computes fit scores by dimension",
            status=scorer_status,
            progress=scorer_progress if active_run_count > 0 else None,
            message=scorer_message,
            items_processed=active_run_count,
            last_run=latest_run_iso,
        ),
        AgentStatusResponse(
            name="orchestrator",
            label="Orchestrator",
            description="Routes tasks and enforces approval gate",
            status=orchestrator_status,
            progress=orch_progress if pending_approvals > 0 and total_approvals > 0 else None,
            message=orchestrator_message,
            items_processed=int(pending_approvals),
            last_run=latest_run_iso,
        ),
    ]


async def build_orchestrator_user_context(session: AsyncSession, user_id: str) -> str:
    """Concise pipeline/profile snapshot used to ground orchestrator chat replies."""
    rows = (
        await session.execute(
            select(Application, Job)
            .join(Job, Job.id == Application.job_id)
            .where(Application.user_id == user_id)
            .order_by(Application.last_updated.desc())
            .limit(6)
        )
    ).all()

    status_rows = (
        await session.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
    ).all()
    status_counts = {str(status): int(count) for status, count in status_rows}

    pending_approvals = (
        await session.execute(
            select(func.count(Approval.id)).where(Approval.user_id == user_id, Approval.status == "pending")
        )
    ).scalar_one()

    if not rows:
        return "No applications in pipeline yet."

    recent_lines = []
    for app, job in rows[:5]:
        recent_lines.append(
            f"- {job.company} — {job.title} (status={app.status}, channel={app.channel})"
        )

    status_text = ", ".join(f"{k}:{v}" for k, v in sorted(status_counts.items()))
    return (
        f"Applications: {len(rows)} recent shown; status mix [{status_text}]. "
        f"Pending approvals: {int(pending_approvals)}.\n"
        f"Recent pipeline items:\n" + "\n".join(recent_lines)
    )
