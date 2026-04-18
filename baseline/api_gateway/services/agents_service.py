from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval
from models.autopilot_run import AutopilotRun
from models.job import Job
from schemas.agents import AgentStatusResponse


async def list_agent_status(session: AsyncSession, user_id: str) -> list[AgentStatusResponse]:
    total_jobs = (await session.execute(select(func.count(Job.id)))).scalar_one()
    pending_approvals = (
        await session.execute(
            select(func.count(Approval.id)).where(Approval.user_id == user_id, Approval.status == "pending")
        )
    ).scalar_one()
    active_runs = (
        await session.execute(
            select(func.count(AutopilotRun.id)).where(
                AutopilotRun.user_id == user_id, AutopilotRun.status.in_(["queued", "running"])
            )
        )
    ).scalar_one()

    return [
        AgentStatusResponse(
            name="discovery",
            label="Discovery agent",
            description="Scans job boards and ATS portals",
            status="active" if total_jobs > 0 else "idle",
            message=f"{total_jobs} indexed jobs",
            items_processed=total_jobs,
        ),
        AgentStatusResponse(
            name="scorer",
            label="Match scorer",
            description="Computes fit scores by dimension",
            status="running" if active_runs > 0 else "idle",
            progress=0.7 if active_runs > 0 else 0.0,
            message="Scoring active pipeline" if active_runs > 0 else "Waiting for new runs",
            items_processed=active_runs,
        ),
        AgentStatusResponse(
            name="orchestrator",
            label="Orchestrator",
            description="Routes tasks and enforces approval gate",
            status="running" if pending_approvals > 0 else "idle",
            progress=0.35 if pending_approvals > 0 else 0.0,
            message=f"{pending_approvals} approvals awaiting action",
            items_processed=pending_approvals,
        ),
    ]
