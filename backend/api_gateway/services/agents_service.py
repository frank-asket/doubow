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

    scorer_progress: float | None = None
    if active_run_count > 0:
        scorer_progress = _autopilot_run_progress(active_runs)

    orch_progress: float | None = None
    if total_approvals > 0:
        orch_progress = (total_approvals - pending_approvals) / total_approvals

    return [
        AgentStatusResponse(
            name="discovery",
            label="Discovery agent",
            description="Scans job boards and ATS portals",
            status="active" if total_jobs > 0 else "idle",
            message=f"{total_jobs} indexed jobs",
            items_processed=int(total_jobs),
        ),
        AgentStatusResponse(
            name="scorer",
            label="Match scorer",
            description="Computes fit scores by dimension",
            status="running" if active_run_count > 0 else "idle",
            progress=scorer_progress if active_run_count > 0 else None,
            message="Scoring active pipeline" if active_run_count > 0 else "Waiting for new runs",
            items_processed=active_run_count,
        ),
        AgentStatusResponse(
            name="orchestrator",
            label="Orchestrator",
            description="Routes tasks and enforces approval gate",
            status="running" if pending_approvals > 0 else "idle",
            progress=orch_progress if pending_approvals > 0 and total_approvals > 0 else None,
            message=f"{pending_approvals} approvals awaiting action",
            items_processed=int(pending_approvals),
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
