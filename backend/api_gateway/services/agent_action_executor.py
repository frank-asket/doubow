from __future__ import annotations

import json
import re
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval import Approval
from models.application import Application
from models.autopilot_run import AutopilotRun
from models.job import Job
from models.job_score import JobScore
from models.prep_session import PrepSession
from models.resume import Resume
from schemas.applications import Channel, CreateApplicationRequest
from services.applications_service import (
    ApplicationIdempotencyConflictError,
    ApplicationJobNotFoundError,
    create_application,
)
from services.approvals_service import (
    ApprovalIdempotencyConflictError,
    approve_approval as approve_approval_service,
    reject_approval as reject_approval_service,
)
from services.draft_service import ApplicationNotFoundError, create_draft_approval_for_application
from services.jobs_service import dismiss_job_for_user, recompute_job_scores_for_user
from services.send_approval_service import schedule_post_approve_dispatch
from services.prep_service import (
    PrepApplicationNotFoundError,
    generate_prep_for_application,
    get_prep_detail_for_user,
    prep_row_to_detail,
)

AgentChannel = Literal["email", "linkedin", "company_site"]

AgentActionName = Literal[
    "get_pipeline_snapshot",
    "list_pending_approvals",
    "get_job_matches",
    "get_application_detail",
    "create_draft_for_application",
    "recompute_job_scores",
    "get_resume_profile_snapshot",
    "get_prep_session_summary",
    "generate_prep_for_application",
    "list_recent_autopilot_runs",
    "queue_job_to_pipeline",
    "dismiss_job_from_discover",
    "approve_outbound_draft",
    "reject_outbound_draft",
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
_RECOMPUTE_HINTS = (
    "recompute",
    "rescore",
    "refresh match",
    "refresh scores",
    "refresh job scores",
    "update match scores",
)
_RESUME_HINTS = (
    "resume summary",
    "parsed resume",
    "what's on my resume",
    "whats on my resume",
    "my resume profile",
    "profile snapshot",
    "resume on file",
)
_PREP_SUMMARY_HINTS = (
    "prep summary",
    "my prep session",
    "show prep",
    "interview prep summary",
    "star stories",
    "company brief",
)
_PREP_GENERATE_HINTS = (
    "generate prep",
    "regenerate prep",
    "build prep",
    "run prep generation",
    "create interview prep",
)
_AUTOPILOT_HINTS = ("autopilot run", "batch run", "scoring run", "recent autopilot", "background run")


class AgentActionCall(BaseModel):
    action: AgentActionName
    limit: int = Field(default=5, ge=1, le=20)
    application_id: str | None = None
    job_id: str | None = None
    approval_id: str | None = None
    channel: AgentChannel | None = None


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

    if lower.startswith("/queue"):
        return AgentActionCall(
            action="queue_job_to_pipeline",
            job_id=_extract_job_id(text),
            channel=_infer_channel(lower),
        )

    if lower.startswith("/dismiss"):
        return AgentActionCall(action="dismiss_job_from_discover", job_id=_extract_job_id(text))

    if lower.startswith("/approve"):
        return AgentActionCall(action="approve_outbound_draft", approval_id=_extract_approval_id_only(text))

    if lower.startswith("/reject"):
        return AgentActionCall(action="reject_outbound_draft", approval_id=_extract_approval_id_only(text))

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

    if lower.startswith("/rescore") or lower.startswith("/recompute") or any(hint in lower for hint in _RECOMPUTE_HINTS):
        return AgentActionCall(action="recompute_job_scores")

    if lower.startswith("/resume") or any(hint in lower for hint in _RESUME_HINTS):
        return AgentActionCall(action="get_resume_profile_snapshot")

    if any(hint in lower for hint in _PREP_GENERATE_HINTS):
        return AgentActionCall(action="generate_prep_for_application", application_id=_extract_application_id(text))

    if lower.startswith("/prep") or any(hint in lower for hint in _PREP_SUMMARY_HINTS):
        return AgentActionCall(action="get_prep_session_summary", application_id=_extract_application_id(text))

    if any(hint in lower for hint in _AUTOPILOT_HINTS):
        return AgentActionCall(action="list_recent_autopilot_runs", limit=_extract_limit(lower))

    jid = _extract_job_id(text)
    if jid:
        if any(p in lower for p in ("add to pipeline", "queue this job", "save to pipeline")):
            return AgentActionCall(
                action="queue_job_to_pipeline",
                job_id=jid,
                channel=_infer_channel(lower),
            )
        if any(p in lower for p in ("dismiss this job", "hide this job", "not interested in this job")):
            return AgentActionCall(action="dismiss_job_from_discover", job_id=jid)

    aid = _extract_approval_id_only(text)
    if aid and any(p in lower for p in ("approve this draft", "approve the draft", "approve outbound draft")):
        return AgentActionCall(action="approve_outbound_draft", approval_id=aid)
    if aid and any(p in lower for p in ("reject this draft", "reject the draft", "discard this draft")):
        return AgentActionCall(action="reject_outbound_draft", approval_id=aid)

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
    if call.action == "recompute_job_scores":
        return await _recompute_job_scores(session=session, user_id=user_id)
    if call.action == "get_resume_profile_snapshot":
        return await _resume_profile_snapshot(session=session, user_id=user_id)
    if call.action == "get_prep_session_summary":
        return await _prep_session_summary(
            session=session, user_id=user_id, application_id=call.application_id
        )
    if call.action == "generate_prep_for_application":
        return await _generate_prep_for_application(session=session, user_id=user_id, application_id=call.application_id)
    if call.action == "list_recent_autopilot_runs":
        return await _recent_autopilot_runs(session=session, user_id=user_id, limit=call.limit)
    if call.action == "queue_job_to_pipeline":
        return await _queue_job_to_pipeline(session=session, user_id=user_id, call=call)
    if call.action == "dismiss_job_from_discover":
        return await _dismiss_job_from_discover(session=session, user_id=user_id, call=call)
    if call.action == "approve_outbound_draft":
        return await _approve_outbound_draft(session=session, user_id=user_id, call=call)
    if call.action == "reject_outbound_draft":
        return await _reject_outbound_draft(session=session, user_id=user_id, call=call)
    raise ValueError(f"Unknown action: {call.action}")


def _extract_application_id(text: str) -> str | None:
    m = re.search(r"\b(app_[a-zA-Z0-9]+)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", text)
    if m:
        return m.group(1)
    return None


def _extract_job_id(text: str) -> str | None:
    m = re.search(r"\b(jb_[a-zA-Z0-9_]+)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", text)
    return m.group(1) if m else None


def _extract_approval_id_only(text: str) -> str | None:
    """Approval rows use UUID primary keys."""
    m = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", text)
    return m.group(1) if m else None


def _infer_channel(lower_text: str) -> AgentChannel | None:
    if "linkedin" in lower_text:
        return "linkedin"
    if "company site" in lower_text or "company_site" in lower_text or "company-site" in lower_text:
        return "company_site"
    if "email" in lower_text:
        return "email"
    return None


def _normalize_channel(ch: AgentChannel | None) -> Channel:
    return ch if ch is not None else "email"


async def _queue_job_to_pipeline(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    if not call.job_id:
        raise AgentActionPolicyError(
            action="queue_job_to_pipeline",
            code="job_id_required",
            detail="Include a job id (jb_* or UUID), e.g. `/queue jb_cat_001 email`.",
        )
    channel = _normalize_channel(call.channel)
    try:
        created = await create_application(
            session,
            user_id,
            CreateApplicationRequest(job_id=call.job_id, channel=channel),
        )
    except ApplicationJobNotFoundError:
        raise AgentActionPolicyError(
            action="queue_job_to_pipeline",
            code="job_not_found",
            detail=f"Job `{call.job_id}` was not found in the catalog.",
        ) from None
    except ApplicationIdempotencyConflictError as exc:
        raise AgentActionPolicyError(
            action="queue_job_to_pipeline",
            code="idempotency_conflict",
            detail=f"Idempotency conflict with existing application `{exc.prior_application_id}`.",
        ) from exc

    body = (
        "Summary:\n"
        f"- Queued job into your pipeline: application `{created.id}` (channel={channel}).\n"
        f"- Role: {created.job.title} @ {created.job.company}.\n"
        "Recommended Actions:\n"
        "- Open Pipeline to track status.\n"
        "- Generate a draft when you are ready to reach out.\n"
        "Why:\n"
        "- Queuing records intent and enables drafting and prep.\n"
        "Next Step:\n"
        "- Open Pipeline or ask for a draft for this application."
    )
    return AgentActionResult(action="queue_job_to_pipeline", response_text=body)


async def _dismiss_job_from_discover(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    if not call.job_id:
        raise AgentActionPolicyError(
            action="dismiss_job_from_discover",
            code="job_id_required",
            detail="Include a job id to dismiss, e.g. `/dismiss jb_cat_001`.",
        )
    try:
        await dismiss_job_for_user(session, user_id, call.job_id)
    except LookupError:
        raise AgentActionPolicyError(
            action="dismiss_job_from_discover",
            code="job_not_found",
            detail=f"Job `{call.job_id}` was not found.",
        ) from None

    body = (
        "Summary:\n"
        f"- Dismissed job `{call.job_id}` from your Discover matches.\n"
        "Recommended Actions:\n"
        "- Refresh Discover to continue reviewing remaining roles.\n"
        "Why:\n"
        "- Dismissals hide roles from your feed without deleting catalog data.\n"
        "Next Step:\n"
        "- Review your next highest-fit match."
    )
    return AgentActionResult(action="dismiss_job_from_discover", response_text=body)


async def _approve_outbound_draft(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    if not call.approval_id:
        raise AgentActionPolicyError(
            action="approve_outbound_draft",
            code="approval_id_required",
            detail="Include an approval id (UUID), e.g. `/approve <uuid>`.",
        )
    try:
        resp = await approve_approval_service(
            session,
            user_id,
            call.approval_id,
            edited_body=None,
            idempotency_key=f"agent-approve-{uuid4().hex}",
        )
        schedule_post_approve_dispatch(
            approval_id=call.approval_id,
            user_id=user_id,
            queued_send=bool(resp.queued_send and resp.send_task_id),
            send_task_id=resp.send_task_id,
        )
    except ApprovalIdempotencyConflictError as exc:
        raise AgentActionPolicyError(
            action="approve_outbound_draft",
            code="idempotency_conflict",
            detail=f"Approval idempotency conflict with `{exc.prior_approval_id}`.",
        ) from exc
    except ValueError:
        raise AgentActionPolicyError(
            action="approve_outbound_draft",
            code="approval_not_found",
            detail=f"Approval `{call.approval_id}` was not found.",
        ) from None

    body = (
        "Summary:\n"
        f"- Approved outbound draft `{call.approval_id}` (status={resp.status}).\n"
        + (
            "- Outbound send has been queued.\n"
            if resp.queued_send
            else "- No new send was queued (already processed or duplicate approval token).\n"
        )
        + "Recommended Actions:\n"
        "- Track delivery from Approvals / Pipeline.\n"
        "Why:\n"
        "- Approval authorizes the same outbound path as the product UI.\n"
        "Next Step:\n"
        "- Confirm delivery or retry from Approvals if needed."
    )
    return AgentActionResult(action="approve_outbound_draft", response_text=body)


async def _reject_outbound_draft(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    if not call.approval_id:
        raise AgentActionPolicyError(
            action="reject_outbound_draft",
            code="approval_id_required",
            detail="Include an approval id (UUID), e.g. `/reject <uuid>`.",
        )
    try:
        await reject_approval_service(session, user_id, call.approval_id)
    except ValueError:
        raise AgentActionPolicyError(
            action="reject_outbound_draft",
            code="approval_not_found",
            detail=f"Approval `{call.approval_id}` was not found.",
        ) from None

    body = (
        "Summary:\n"
        f"- Rejected and removed pending approval `{call.approval_id}`.\n"
        "Recommended Actions:\n"
        "- Generate a new draft from Pipeline if you still want to reach out.\n"
        "Why:\n"
        "- Reject removes the draft without sending.\n"
        "Next Step:\n"
        "- Continue reviewing remaining approvals."
    )
    return AgentActionResult(action="reject_outbound_draft", response_text=body)


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


async def _recompute_job_scores(*, session: AsyncSession, user_id: str) -> AgentActionResult:
    n = await recompute_job_scores_for_user(session, user_id)
    body = (
        "Summary:\n"
        f"- Refreshed job fit scores for {n} job row(s) tied to your profile.\n"
        "Recommended Actions:\n"
        "- Open Discover and verify top matches reflect your latest resume.\n"
        "- Queue high-fit roles while scores are fresh.\n"
        "Why:\n"
        "- Scores blend lexical and (when enabled) semantic signals against your stored profile.\n"
        "Next Step:\n"
        "- Review your top 5 matches in Discover now."
    )
    return AgentActionResult(action="recompute_job_scores", response_text=body)


async def _resume_profile_snapshot(*, session: AsyncSession, user_id: str) -> AgentActionResult:
    row = (
        await session.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        body = (
            "Summary:\n"
            "- No resume file is stored yet.\n"
            "Recommended Actions:\n"
            "- Upload a resume from the Resume screen.\n"
            "Why:\n"
            "- Parsing profile data drives matching and drafts.\n"
            "Next Step:\n"
            "- Upload your resume (PDF or DOCX)."
        )
        return AgentActionResult(action="get_resume_profile_snapshot", response_text=body)

    profile_excerpt = ""
    if isinstance(row.parsed_profile, dict) and row.parsed_profile:
        raw = json.dumps(row.parsed_profile, ensure_ascii=False)
        profile_excerpt = raw[:2400] + ("…" if len(raw) > 2400 else "")
    pref_excerpt = ""
    if isinstance(row.preferences, dict) and row.preferences:
        rawp = json.dumps(row.preferences, ensure_ascii=False)
        pref_excerpt = rawp[:1200] + ("…" if len(rawp) > 1200 else "")

    body = (
        "Summary:\n"
        f"- Latest resume on file: `{row.file_name}` (version {row.version}).\n"
        + (
            f"- Parsed profile (excerpt):\n{profile_excerpt}\n"
            if profile_excerpt
            else "- Parsed profile is empty — consider re-uploading a clearer file.\n"
        )
        + (
            f"- Stated preferences:\n{pref_excerpt}\n"
            if pref_excerpt
            else ""
        )
        + "Recommended Actions:\n"
        "- Align preferences with target roles and locations.\n"
        "- Trigger a score refresh after substantive edits.\n"
        "Why:\n"
        "- Drafts and matching ground on this snapshot.\n"
        "Next Step:\n"
        "- Say “refresh my matches” after any preference change."
    )
    return AgentActionResult(action="get_resume_profile_snapshot", response_text=body)


async def _prep_session_summary(
    *,
    session: AsyncSession,
    user_id: str,
    application_id: str | None,
) -> AgentActionResult:
    target_app = application_id
    if not target_app:
        prep_row = (
            await session.execute(
                select(PrepSession)
                .join(Application, Application.id == PrepSession.application_id)
                .where(Application.user_id == user_id)
                .order_by(PrepSession.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if prep_row is None:
            body = (
                "Summary:\n"
                "- No interview prep sessions found yet.\n"
                "Recommended Actions:\n"
                "- Open Prep from an application and generate prep.\n"
                "Why:\n"
                "- Prep is generated per application.\n"
                "Next Step:\n"
                "- Queue an application, then ask to generate interview prep for it."
            )
            return AgentActionResult(action="get_prep_session_summary", response_text=body)
        detail = await prep_row_to_detail(session, user_id, prep_row)
    else:
        detail = await get_prep_detail_for_user(session, user_id, target_app)
        if detail is None:
            body = (
                "Summary:\n"
                f"- No prep session for application `{target_app}`.\n"
                "Recommended Actions:\n"
                "- Generate prep for that application first.\n"
                "Why:\n"
                "- Prep rows are created when you run Prep > Generate.\n"
                "Next Step:\n"
                "- Ask to generate interview prep for that application."
            )
            return AgentActionResult(action="get_prep_session_summary", response_text=body)

    n_q = len(detail.questions or [])
    n_star = len(detail.star_stories or [])
    brief = (detail.company_brief or "").strip()
    brief_snip = brief[:900] + ("…" if len(brief) > 900 else "")
    title_line = f"{detail.application.job.title} @ {detail.application.job.company}"
    body = (
        "Summary:\n"
        f"- Prep for `{title_line}` (application `{detail.application.id}`).\n"
        f"- Questions: {n_q}; STAR stories: {n_star}.\n"
        f"- Company brief (excerpt):\n{brief_snip if brief_snip else '(empty)'}\n"
        "Recommended Actions:\n"
        "- Rehearse STAR stories aloud with timers.\n"
        "- Cross-check claims against your resume facts.\n"
        "Why:\n"
        "- Grounded prep improves signal in interviews.\n"
        "Next Step:\n"
        "- Drill one STAR story end-to-end."
    )
    return AgentActionResult(action="get_prep_session_summary", response_text=body)


async def _latest_application_id(session: AsyncSession, user_id: str) -> str | None:
    row = (
        await session.execute(
            select(Application.id)
            .where(Application.user_id == user_id)
            .order_by(Application.last_updated.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return str(row) if row else None


async def _generate_prep_for_application(
    *,
    session: AsyncSession,
    user_id: str,
    application_id: str | None,
) -> AgentActionResult:
    app_id = application_id or await _latest_application_id(session, user_id)
    if not app_id:
        raise AgentActionPolicyError(
            action="generate_prep_for_application",
            code="application_id_required",
            detail="Policy blocked: specify an application id (app_*) or add at least one application to your pipeline.",
        )
    try:
        detail = await generate_prep_for_application(session, user_id, app_id)
    except PrepApplicationNotFoundError:
        raise AgentActionPolicyError(
            action="generate_prep_for_application",
            code="application_not_found",
            detail=f"Policy blocked: application `{app_id}` was not found in your pipeline.",
        ) from None

    n_q = len(detail.questions or [])
    n_star = len(detail.star_stories or [])
    body = (
        "Summary:\n"
        f"- Generated fresh interview prep for application `{app_id}` (prep id `{detail.id}`).\n"
        f"- Questions: {n_q}; STAR stories: {n_star}.\n"
        "Recommended Actions:\n"
        "- Open the Prep tab for this application to review full content.\n"
        "- Regenerate only if the job description changed materially.\n"
        "Why:\n"
        "- Prep consumes LLM quota and overwrites the latest session for that application.\n"
        "Next Step:\n"
        "- Rehearse the first STAR story aloud."
    )
    return AgentActionResult(action="generate_prep_for_application", response_text=body)


async def _recent_autopilot_runs(
    *,
    session: AsyncSession,
    user_id: str,
    limit: int,
) -> AgentActionResult:
    limit = max(1, min(20, limit))
    rows = (
        await session.execute(
            select(AutopilotRun)
            .where(AutopilotRun.user_id == user_id)
            .order_by(AutopilotRun.started_at.desc().nulls_last(), AutopilotRun.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    if not rows:
        body = (
            "Summary:\n"
            "- No autopilot runs recorded yet.\n"
            "Recommended Actions:\n"
            "- Start autopilot from the product when you have queued applications.\n"
            "Why:\n"
            "- Batch drafting and scoring show up here.\n"
            "Next Step:\n"
            "- Queue applications, then run autopilot."
        )
        return AgentActionResult(action="list_recent_autopilot_runs", response_text=body)

    lines = []
    for r in rows:
        detail = (r.failure_detail or "")[:120]
        lines.append(
            f"- run `{r.id}` status={r.status} scope={r.scope} "
            f"started={r.started_at.isoformat() if r.started_at else 'n/a'} "
            f"fail={detail or 'none'}"
        )
    body = (
        "Summary:\n"
        f"- Showing {len(rows)} recent autopilot run(s).\n"
        "Recommended Actions:\n"
        "- If a run is stuck `running` with a checkpoint, use Resume from the Assistant/API.\n"
        "- Retry failed runs after fixing upstream issues.\n"
        "Why:\n"
        "- Background runs can fail when LLM or mail prerequisites are missing.\n"
        "Next Step:\n"
        "- Open Approvals if the last run produced drafts.\n\n"
        + "\n".join(lines)
    )
    return AgentActionResult(action="list_recent_autopilot_runs", response_text=body)
