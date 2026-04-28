from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval
from models.application import Application
from models.job import Job

AgentActionName = Literal["get_pipeline_snapshot", "list_pending_approvals"]

_PIPELINE_HINTS = (
    "pipeline summary",
    "pipeline status",
    "status mix",
    "application status",
    "show pipeline",
)
_APPROVAL_HINTS = (
    "pending approvals",
    "approval queue",
    "approvals queue",
    "show approvals",
)


class AgentActionCall(BaseModel):
    action: AgentActionName
    limit: int = Field(default=5, ge=1, le=20)


class AgentActionResult(BaseModel):
    action: AgentActionName
    response_text: str


def infer_action_from_message(message: str) -> AgentActionCall | None:
    text = (message or "").strip()
    lower = text.lower()
    if not lower:
        return None

    if lower.startswith("/pipeline") or any(hint in lower for hint in _PIPELINE_HINTS):
        return AgentActionCall(action="get_pipeline_snapshot")

    if lower.startswith("/approvals") or any(hint in lower for hint in _APPROVAL_HINTS):
        return AgentActionCall(action="list_pending_approvals", limit=_extract_limit(lower))

    return None


def _extract_limit(lower_text: str) -> int:
    m = re.search(r"\btop\s+(\d{1,2})\b", lower_text)
    if not m:
        m = re.search(r"\b(\d{1,2})\s+approvals?\b", lower_text)
    if not m:
        return 5
    try:
        value = int(m.group(1))
    except Exception:
        return 5
    return max(1, min(20, value))


async def execute_action(
    *,
    session: AsyncSession,
    user_id: str,
    call: AgentActionCall,
) -> AgentActionResult:
    if call.action == "get_pipeline_snapshot":
        return await _pipeline_snapshot(session=session, user_id=user_id)
    if call.action == "list_pending_approvals":
        return await _pending_approvals(session=session, user_id=user_id, limit=call.limit)
    raise ValueError(f"Unknown action: {call.action}")


async def _pipeline_snapshot(*, session: AsyncSession, user_id: str) -> AgentActionResult:
    status_rows = (
        await session.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
    ).all()
    status_counts = {str(status): int(count) for status, count in status_rows}
    total_apps = sum(status_counts.values())
    pending_approvals = (
        await session.execute(
            select(func.count(Approval.id)).where(Approval.user_id == user_id, Approval.status == "pending")
        )
    ).scalar_one()
    recent_rows = (
        await session.execute(
            select(Application.status, Application.channel, Job.company, Job.title)
            .join(Job, Job.id == Application.job_id)
            .where(Application.user_id == user_id)
            .order_by(Application.last_updated.desc())
            .limit(3)
        )
    ).all()

    if total_apps == 0:
        body = (
            "Summary:\n"
            "- You do not have applications in the pipeline yet.\n"
            "Recommended Actions:\n"
            "- Queue a few high-fit jobs from Discover to create your pipeline baseline.\n"
            "- Run autopilot draft generation once you have queued applications.\n"
            "Why:\n"
            "- Pipeline insights become useful only after at least one application exists.\n"
            "Next Step:\n"
            "- Queue your first 3 jobs from Discover."
        )
        return AgentActionResult(action="get_pipeline_snapshot", response_text=body)

    status_text = ", ".join(f"{k}:{v}" for k, v in sorted(status_counts.items()))
    recent_lines = [
        f"- {company} — {title} (status={status}, channel={channel})"
        for status, channel, company, title in recent_rows
    ]
    if not recent_lines:
        recent_lines = ["- No recent pipeline items found."]

    body = (
        "Summary:\n"
        f"- Pipeline snapshot: {total_apps} applications; status mix [{status_text}].\n"
        f"- Pending approvals waiting for action: {int(pending_approvals)}.\n"
        "Recommended Actions:\n"
        "- Prioritize pending approvals first to unblock outreach delivery.\n"
        "- Review the most recent applications for stalled statuses and update next actions.\n"
        "Why:\n"
        "- Approval backlog directly delays outbound progress and response velocity.\n"
        "Next Step:\n"
        "- Clear at least 1 pending approval now.\n\n"
        "Recent pipeline items:\n"
        + "\n".join(recent_lines)
    )
    return AgentActionResult(action="get_pipeline_snapshot", response_text=body)


async def _pending_approvals(
    *,
    session: AsyncSession,
    user_id: str,
    limit: int,
) -> AgentActionResult:
    rows = (
        await session.execute(
            select(Approval.id, Approval.type, Approval.channel, Job.company, Job.title)
            .join(Application, Application.id == Approval.application_id)
            .join(Job, Job.id == Application.job_id)
            .where(Approval.user_id == user_id, Approval.status == "pending")
            .order_by(Approval.created_at.desc())
            .limit(limit)
        )
    ).all()
    total_pending = (
        await session.execute(
            select(func.count(Approval.id)).where(Approval.user_id == user_id, Approval.status == "pending")
        )
    ).scalar_one()

    if total_pending == 0:
        body = (
            "Summary:\n"
            "- There are no pending approvals right now.\n"
            "Recommended Actions:\n"
            "- Run autopilot on your latest queued applications to generate fresh drafts.\n"
            "Why:\n"
            "- Keeping approvals at zero means your send queue is currently clear.\n"
            "Next Step:\n"
            "- Start an autopilot run for newly queued applications."
        )
        return AgentActionResult(action="list_pending_approvals", response_text=body)

    lines = [f"- {company} — {title} [{atype}/{channel}] (approval_id={aid})" for aid, atype, channel, company, title in rows]
    body = (
        "Summary:\n"
        f"- You have {int(total_pending)} pending approvals.\n"
        f"- Showing the latest {len(rows)} approvals.\n"
        "Recommended Actions:\n"
        "- Approve highest-priority roles first to unblock delivery.\n"
        "- Edit any draft that needs personalization before approving.\n"
        "Why:\n"
        "- Pending approvals are a hard gate before outreach can be sent.\n"
        "Next Step:\n"
        "- Open the top approval and approve or edit it now.\n\n"
        "Pending approval queue:\n"
        + "\n".join(lines)
    )
    return AgentActionResult(action="list_pending_approvals", response_text=body)
