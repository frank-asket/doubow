from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval
from models.application import Application
from models.job import Job
from models.job_score import JobScore
from services.draft_service import ApplicationNotFoundError, create_draft_approval_for_application

AgentActionName = Literal[
    "get_pipeline_snapshot",
    "list_pending_approvals",
    "get_job_matches",
    "get_application_detail",
    "create_draft_for_application",
]

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
_MATCH_HINTS = ("job matches", "top matches", "best matches", "fit matches", "match summary")
_APPLICATION_HINTS = ("application detail", "application status", "show application", "latest application")
_DRAFT_HINTS = ("create draft", "draft approval", "generate draft", "make draft", "new draft")


class AgentActionCall(BaseModel):
    action: AgentActionName
    limit: int = Field(default=5, ge=1, le=20)
    application_id: str | None = None


class AgentActionResult(BaseModel):
    action: AgentActionName
    response_text: str


class AgentActionPolicyError(ValueError):
    def __init__(self, *, action: AgentActionName, code: str, detail: str) -> None:
        super().__init__(detail)
        self.action = action
        self.code = code
        self.detail = detail


def infer_action_from_message(message: str) -> AgentActionCall | None:
    text = (message or "").strip()
    lower = text.lower()
    if not lower:
        return None

    if lower.startswith("/pipeline") or any(hint in lower for hint in _PIPELINE_HINTS):
        return AgentActionCall(action="get_pipeline_snapshot")

    if lower.startswith("/approvals") or any(hint in lower for hint in _APPROVAL_HINTS):
        return AgentActionCall(action="list_pending_approvals", limit=_extract_limit(lower))

    if lower.startswith("/matches") or any(hint in lower for hint in _MATCH_HINTS):
        return AgentActionCall(action="get_job_matches", limit=_extract_limit(lower))

    if lower.startswith("/application") or any(hint in lower for hint in _APPLICATION_HINTS):
        return AgentActionCall(action="get_application_detail", application_id=_extract_application_id(text))

    if lower.startswith("/draft") or any(hint in lower for hint in _DRAFT_HINTS):
        return AgentActionCall(action="create_draft_for_application", application_id=_extract_application_id(text))

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
    if call.action == "get_job_matches":
        return await _job_matches(session=session, user_id=user_id, limit=call.limit)
    if call.action == "get_application_detail":
        return await _application_detail(session=session, user_id=user_id, application_id=call.application_id)
    if call.action == "create_draft_for_application":
        return await _create_draft_for_application(session=session, user_id=user_id, application_id=call.application_id)
    raise ValueError(f"Unknown action: {call.action}")


def _extract_application_id(text: str) -> str | None:
    m = re.search(r"\b(app_[a-zA-Z0-9]+)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", text)
    if m:
        return m.group(1)
    return None


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


async def _job_matches(*, session: AsyncSession, user_id: str, limit: int) -> AgentActionResult:
    rows = (
        await session.execute(
            select(Job.company, Job.title, Job.location, JobScore.fit_score, JobScore.risk_flags)
            .join(Job, Job.id == JobScore.job_id)
            .where(JobScore.user_id == user_id)
            .order_by(JobScore.fit_score.desc(), JobScore.scored_at.desc())
            .limit(limit)
        )
    ).all()
    total_scored = (
        await session.execute(select(func.count(JobScore.id)).where(JobScore.user_id == user_id))
    ).scalar_one()

    if total_scored == 0:
        body = (
            "Summary:\n"
            "- No scored job matches are available yet.\n"
            "Recommended Actions:\n"
            "- Upload or refresh your resume profile to trigger scoring.\n"
            "- Open Discover and queue roles so the scorer has data to rank.\n"
            "Why:\n"
            "- Match ranking requires scored jobs tied to your user profile.\n"
            "Next Step:\n"
            "- Open Discover and queue 3 roles for scoring."
        )
        return AgentActionResult(action="get_job_matches", response_text=body)

    lines: list[str] = []
    for company, title, location, fit_score, risk_flags in rows:
        risks = ", ".join((risk_flags or [])[:2]) if isinstance(risk_flags, list) and risk_flags else "none"
        lines.append(f"- {company} — {title} ({location or 'unspecified'}) fit={float(fit_score):.1f}/5 risk_flags={risks}")

    body = (
        "Summary:\n"
        f"- You have {int(total_scored)} scored jobs; showing top {len(rows)} matches.\n"
        "Recommended Actions:\n"
        "- Queue the top 1-2 high-fit roles immediately.\n"
        "- Review risk flags before approving outbound drafts.\n"
        "Why:\n"
        "- Acting on highest-fit roles first improves pipeline conversion speed.\n"
        "Next Step:\n"
        "- Queue your top match now.\n\n"
        "Top matches:\n"
        + "\n".join(lines)
    )
    return AgentActionResult(action="get_job_matches", response_text=body)


async def _application_detail(
    *,
    session: AsyncSession,
    user_id: str,
    application_id: str | None,
) -> AgentActionResult:
    stmt = (
        select(Application.id, Application.status, Application.channel, Application.last_updated, Job.company, Job.title)
        .join(Job, Job.id == Application.job_id)
        .where(Application.user_id == user_id)
    )
    if application_id:
        stmt = stmt.where(Application.id == application_id)
    stmt = stmt.order_by(Application.last_updated.desc()).limit(1)
    row = (await session.execute(stmt)).first()
    if row is None:
        body = (
            "Summary:\n"
            "- No matching application was found for your request.\n"
            "Recommended Actions:\n"
            "- Verify the application id or ask for your latest application detail.\n"
            "Why:\n"
            "- Application detail can only be shown for records in your pipeline.\n"
            "Next Step:\n"
            "- Ask: show my latest application detail."
        )
        return AgentActionResult(action="get_application_detail", response_text=body)

    app_id, app_status, channel, last_updated, company, title = row
    approval_rows = (
        await session.execute(
            select(Approval.status, Approval.delivery_status, Approval.type)
            .where(Approval.user_id == user_id, Approval.application_id == app_id)
            .order_by(Approval.created_at.desc())
            .limit(3)
        )
    ).all()
    pending_for_app = sum(1 for st, _, _ in approval_rows if st == "pending")
    approval_lines = [
        f"- {atype}: status={st}, delivery={delivery}"
        for st, delivery, atype in approval_rows
    ]
    if not approval_lines:
        approval_lines = ["- No approvals generated for this application yet."]

    body = (
        "Summary:\n"
        f"- Application {app_id}: {company} — {title}.\n"
        f"- Status={app_status}, channel={channel}, last_updated={last_updated.isoformat()}.\n"
        "Recommended Actions:\n"
        + (
            "- Resolve pending approvals for this application first.\n"
            if pending_for_app > 0
            else "- Generate or review draft approvals for this application.\n"
        )
        + "- Keep application notes updated after each outbound step.\n"
        "Why:\n"
        "- Accurate per-application state prevents duplicate or stalled outreach.\n"
        "Next Step:\n"
        + (
            "- Open the pending approval for this application now."
            if pending_for_app > 0
            else "- Generate a draft approval for this application now."
        )
        + "\n\nLatest approvals:\n"
        + "\n".join(approval_lines)
    )
    return AgentActionResult(action="get_application_detail", response_text=body)


async def _create_draft_for_application(
    *,
    session: AsyncSession,
    user_id: str,
    application_id: str | None,
) -> AgentActionResult:
    if not application_id:
        raise AgentActionPolicyError(
            action="create_draft_for_application",
            code="application_id_required",
            detail="Policy blocked: include an application id (for example app_xxx) to create a draft.",
        )

    app_row = (
        await session.execute(
            select(Application).where(Application.id == application_id, Application.user_id == user_id).limit(1)
        )
    ).scalar_one_or_none()
    if app_row is None:
        raise AgentActionPolicyError(
            action="create_draft_for_application",
            code="application_not_found",
            detail=f"Policy blocked: application `{application_id}` was not found in your pipeline.",
        )
    if bool(app_row.is_stale):
        raise AgentActionPolicyError(
            action="create_draft_for_application",
            code="application_stale",
            detail=f"Policy blocked: application `{application_id}` is marked stale. Refresh or deduplicate before drafting.",
        )
    if str(app_row.status).lower() in {"rejected"}:
        raise AgentActionPolicyError(
            action="create_draft_for_application",
            code="application_closed",
            detail=f"Policy blocked: application `{application_id}` is in `{app_row.status}` state.",
        )
    existing_pending = (
        await session.execute(
            select(Approval.id).where(Approval.application_id == application_id, Approval.user_id == user_id, Approval.status == "pending").limit(1)
        )
    ).scalar_one_or_none()
    if existing_pending:
        raise AgentActionPolicyError(
            action="create_draft_for_application",
            code="pending_approval_exists",
            detail=(
                f"Policy blocked: a pending approval already exists for `{application_id}` "
                f"(approval_id={existing_pending})."
            ),
        )

    try:
        approval = await create_draft_approval_for_application(session, user_id, application_id)
    except ApplicationNotFoundError as exc:
        raise AgentActionPolicyError(
            action="create_draft_for_application",
            code="application_not_found",
            detail=f"Policy blocked: application `{application_id}` was not found in your pipeline.",
        ) from exc

    body = (
        "Summary:\n"
        f"- Draft approval created for application `{application_id}`.\n"
        f"- Approval id: `{approval.id}` ({approval.type}/{approval.channel}).\n"
        "Recommended Actions:\n"
        "- Review and edit the draft body if needed.\n"
        "- Approve outreach when ready.\n"
        "Why:\n"
        "- Draft creation prepares a controlled approval step before any outbound send.\n"
        "Next Step:\n"
        "- Open the new approval and approve or edit it now."
    )
    return AgentActionResult(action="create_draft_for_application", response_text=body)
