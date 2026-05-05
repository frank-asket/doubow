from __future__ import annotations

import json
from typing import Literal

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
from config import settings as app_settings
from services.draft_service import ApplicationNotFoundError, create_draft_approval_for_application
from services.jobs_service import recompute_job_scores_for_user
from services.agent_action_approvals import (
    ApprovalActionError,
    approve_outbound_draft_action,
    reject_outbound_draft_action,
)
from services.agent_action_pipeline import (
    PipelineActionError,
    dismiss_job_from_discover_action,
    pipeline_snapshot_action,
    queue_job_to_pipeline_action,
    run_job_search_pipeline_action,
)
from services.prep_service import (
    PrepApplicationNotFoundError,
    generate_prep_for_application,
    get_prep_detail_for_user,
    prep_row_to_detail,
)
from services.agent_action_inference import (
    APPLICATION_HINTS,
    APPROVAL_HINTS,
    AUTOPILOT_HINTS,
    DRAFT_HINTS,
    MATCH_HINTS,
    PIPELINE_HINTS,
    PIPELINE_RUN_HINTS,
    PREP_GENERATE_HINTS,
    PREP_SUMMARY_HINTS,
    RECOMPUTE_HINTS,
    RESUME_HINTS,
    extract_application_id,
    extract_approval_id_only,
    extract_job_id,
    extract_limit,
    infer_channel,
)

AgentChannel = Literal["email", "linkedin", "company_site"]
CatalogPreset = Literal["hourly", "daily"]

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
    "run_job_search_pipeline",
]

class AgentActionCall(BaseModel):
    action: AgentActionName
    limit: int = Field(default=5, ge=1, le=20)
    application_id: str | None = None
    job_id: str | None = None
    approval_id: str | None = None
    channel: AgentChannel | None = None
    trigger_catalog_refresh: bool = False
    persist_feedback_learning: bool = False
    catalog_preset: CatalogPreset = "hourly"
    include_legacy_connectors: bool = False
    include_scrapling: bool = True
    resume_aligned_catalog: bool = True
    pipeline_stages: list[str] | None = None


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

    if lower.startswith("/pipeline-run"):
        rest = lower[len("/pipeline-run") :].strip()
        trig = "--refresh" in rest or " refresh" in f" {rest} "
        persist = "--persist-feedback" in rest or "--learn" in rest
        return AgentActionCall(
            action="run_job_search_pipeline",
            trigger_catalog_refresh=trig,
            persist_feedback_learning=persist,
        )

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

    if any(hint in lower for hint in PIPELINE_RUN_HINTS):
        trig = "catalog refresh" in lower or "refresh catalog" in lower
        persist = "persist feedback" in lower or "save feedback" in lower or "learn from outcomes" in lower
        return AgentActionCall(
            action="run_job_search_pipeline",
            trigger_catalog_refresh=trig,
            persist_feedback_learning=persist,
        )

    if lower.startswith("/pipeline") or any(hint in lower for hint in PIPELINE_HINTS):
        return AgentActionCall(action="get_pipeline_snapshot")

    if lower.startswith("/approvals") or any(hint in lower for hint in APPROVAL_HINTS):
        return AgentActionCall(action="list_pending_approvals", limit=extract_limit(lower))

    if lower.startswith("/matches") or any(hint in lower for hint in MATCH_HINTS):
        return AgentActionCall(action="get_job_matches", limit=extract_limit(lower))

    if lower.startswith("/application") or any(hint in lower for hint in APPLICATION_HINTS):
        return AgentActionCall(action="get_application_detail", application_id=extract_application_id(text))

    if lower.startswith("/draft") or any(hint in lower for hint in DRAFT_HINTS):
        return AgentActionCall(action="create_draft_for_application", application_id=extract_application_id(text))

    if lower.startswith("/rescore") or lower.startswith("/recompute") or any(hint in lower for hint in RECOMPUTE_HINTS):
        return AgentActionCall(action="recompute_job_scores")

    if lower.startswith("/resume") or any(hint in lower for hint in RESUME_HINTS):
        return AgentActionCall(action="get_resume_profile_snapshot")

    if any(hint in lower for hint in PREP_GENERATE_HINTS):
        return AgentActionCall(action="generate_prep_for_application", application_id=extract_application_id(text))

    if lower.startswith("/prep") or any(hint in lower for hint in PREP_SUMMARY_HINTS):
        return AgentActionCall(action="get_prep_session_summary", application_id=extract_application_id(text))

    if any(hint in lower for hint in AUTOPILOT_HINTS):
        return AgentActionCall(action="list_recent_autopilot_runs", limit=extract_limit(lower))

    jid = extract_job_id(text)
    if jid:
        if any(p in lower for p in ("add to pipeline", "queue this job", "save to pipeline")):
            return AgentActionCall(
                action="queue_job_to_pipeline",
                job_id=jid,
                channel=infer_channel(lower),
            )
        if any(p in lower for p in ("dismiss this job", "hide this job", "not interested in this job")):
            return AgentActionCall(action="dismiss_job_from_discover", job_id=jid)

    aid = extract_approval_id_only(text)
    if aid and any(p in lower for p in ("approve this draft", "approve the draft", "approve outbound draft")):
        return AgentActionCall(action="approve_outbound_draft", approval_id=aid)
    if aid and any(p in lower for p in ("reject this draft", "reject the draft", "discard this draft")):
        return AgentActionCall(action="reject_outbound_draft", approval_id=aid)

    return None


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
    if call.action == "run_job_search_pipeline":
        return await _run_job_search_pipeline(session=session, user_id=user_id, call=call)
    raise ValueError(f"Unknown action: {call.action}")


async def _run_job_search_pipeline(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    try:
        body = await run_job_search_pipeline_action(
            session=session,
            user_id=user_id,
            pipeline_stages=call.pipeline_stages,
            trigger_catalog_refresh=call.trigger_catalog_refresh,
            persist_feedback_learning=call.persist_feedback_learning,
            catalog_preset=call.catalog_preset,
            include_legacy_connectors=call.include_legacy_connectors,
            include_scrapling=call.include_scrapling,
            resume_aligned_catalog=call.resume_aligned_catalog,
            settings=app_settings,
        )
    except PipelineActionError as exc:
        raise AgentActionPolicyError(
            action="run_job_search_pipeline",
            code=exc.code,
            detail=exc.detail,
        ) from exc
    return AgentActionResult(action="run_job_search_pipeline", response_text=body)


def _extract_application_id(text: str) -> str | None:
    return extract_application_id(text)


def _extract_job_id(text: str) -> str | None:
    return extract_job_id(text)


def _extract_approval_id_only(text: str) -> str | None:
    return extract_approval_id_only(text)


def _infer_channel(lower_text: str) -> AgentChannel | None:
    return infer_channel(lower_text)


async def _queue_job_to_pipeline(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    try:
        body = await queue_job_to_pipeline_action(
            session=session,
            user_id=user_id,
            job_id=call.job_id,
            channel=call.channel,
        )
    except PipelineActionError as exc:
        raise AgentActionPolicyError(
            action="queue_job_to_pipeline",
            code=exc.code,
            detail=exc.detail,
        ) from exc
    return AgentActionResult(action="queue_job_to_pipeline", response_text=body)


async def _dismiss_job_from_discover(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    try:
        body = await dismiss_job_from_discover_action(
            session=session,
            user_id=user_id,
            job_id=call.job_id,
        )
    except PipelineActionError as exc:
        raise AgentActionPolicyError(
            action="dismiss_job_from_discover",
            code=exc.code,
            detail=exc.detail,
        ) from exc
    return AgentActionResult(action="dismiss_job_from_discover", response_text=body)


async def _approve_outbound_draft(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    try:
        body = await approve_outbound_draft_action(
            session=session,
            user_id=user_id,
            approval_id=call.approval_id,
        )
    except ApprovalActionError as exc:
        raise AgentActionPolicyError(
            action="approve_outbound_draft",
            code=exc.code,
            detail=exc.detail,
        ) from exc
    return AgentActionResult(action="approve_outbound_draft", response_text=body)


async def _reject_outbound_draft(
    *, session: AsyncSession, user_id: str, call: AgentActionCall
) -> AgentActionResult:
    try:
        body = await reject_outbound_draft_action(
            session=session,
            user_id=user_id,
            approval_id=call.approval_id,
        )
    except ApprovalActionError as exc:
        raise AgentActionPolicyError(
            action="reject_outbound_draft",
            code=exc.code,
            detail=exc.detail,
        ) from exc
    return AgentActionResult(action="reject_outbound_draft", response_text=body)


async def _pipeline_snapshot(*, session: AsyncSession, user_id: str) -> AgentActionResult:
    body = await pipeline_snapshot_action(session=session, user_id=user_id)
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
