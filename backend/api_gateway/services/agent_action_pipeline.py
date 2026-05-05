from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic_settings import BaseSettings
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.approval import Approval
from models.job import Job
from schemas.applications import Channel, CreateApplicationRequest
from schemas.job_search_pipeline import JobSearchPipelineRunRequest, JobSearchPipelineStageId
from services.applications_service import (
    ApplicationIdempotencyConflictError,
    ApplicationJobNotFoundError,
    create_application,
)
from services.job_search_pipeline import coordinator as job_search_pipeline_coordinator
from services.jobs_service import dismiss_job_for_user

AgentChannel = Literal["email", "linkedin", "company_site"]


@dataclass
class PipelineActionError(Exception):
    code: str
    detail: str


def _normalize_channel(ch: AgentChannel | None) -> Channel:
    return ch if ch is not None else "email"


async def run_job_search_pipeline_action(
    *,
    session: AsyncSession,
    user_id: str,
    pipeline_stages: list[str] | None,
    trigger_catalog_refresh: bool,
    persist_feedback_learning: bool,
    catalog_preset: Literal["hourly", "daily"],
    include_legacy_connectors: bool,
    include_scrapling: bool,
    resume_aligned_catalog: bool,
    settings: BaseSettings,
) -> str:
    stages = None
    if pipeline_stages:
        parsed: list[JobSearchPipelineStageId] = []
        for s in pipeline_stages:
            try:
                parsed.append(JobSearchPipelineStageId(s))
            except ValueError as exc:
                raise PipelineActionError(
                    code="invalid_stage",
                    detail=f"Unknown pipeline stage {s!r}. Expected one of: "
                    + ", ".join(e.value for e in JobSearchPipelineStageId),
                ) from exc
        stages = parsed

    body = JobSearchPipelineRunRequest(
        stages=stages,
        trigger_catalog_refresh=trigger_catalog_refresh,
        persist_feedback_learning=persist_feedback_learning,
        catalog_preset=catalog_preset,
        include_legacy_connectors=include_legacy_connectors,
        include_scrapling=include_scrapling,
        resume_aligned_catalog=resume_aligned_catalog,
    )
    res = await job_search_pipeline_coordinator.run(session, settings, user_id, body)
    lines = [
        "Summary:",
        f"- Ran job search pipeline (trace {res.trace_id}).",
        "",
        "Stages:",
    ]
    for st in res.stages:
        status = "ok" if st.ok else "failed"
        lines.append(f"- {st.stage.value} ({status}): {st.summary}")
        if st.error:
            lines.append(f"  error: {st.error}")
    lines.extend(
        [
            "",
            "Recommended Actions:",
            "- Review any failed stages and fix configuration (e.g. catalog ingest env vars).",
            "- Use Discover and Pipeline if matching scores were refreshed.",
            "",
            "Next Step:",
            "- Ask for a pipeline summary or top matches to continue.",
        ]
    )
    return "\n".join(lines)


async def queue_job_to_pipeline_action(
    *,
    session: AsyncSession,
    user_id: str,
    job_id: str | None,
    channel: AgentChannel | None,
) -> str:
    if not job_id:
        raise PipelineActionError(
            code="job_id_required",
            detail="Include a job id (jb_* or UUID), e.g. `/queue jb_cat_001 email`.",
        )
    normalized_channel = _normalize_channel(channel)
    try:
        created = await create_application(
            session,
            user_id,
            CreateApplicationRequest(job_id=job_id, channel=normalized_channel),
        )
    except ApplicationJobNotFoundError:
        raise PipelineActionError(
            code="job_not_found",
            detail=f"Job `{job_id}` was not found in the catalog.",
        ) from None
    except ApplicationIdempotencyConflictError as exc:
        raise PipelineActionError(
            code="idempotency_conflict",
            detail=f"Idempotency conflict with existing application `{exc.prior_application_id}`.",
        ) from exc

    return (
        "Summary:\n"
        f"- Queued job into your pipeline: application `{created.id}` (channel={normalized_channel}).\n"
        f"- Role: {created.job.title} @ {created.job.company}.\n"
        "Recommended Actions:\n"
        "- Open Pipeline to track status.\n"
        "- Generate a draft when you are ready to reach out.\n"
        "Why:\n"
        "- Queuing records intent and enables drafting and prep.\n"
        "Next Step:\n"
        "- Open Pipeline or ask for a draft for this application."
    )


async def dismiss_job_from_discover_action(
    *,
    session: AsyncSession,
    user_id: str,
    job_id: str | None,
) -> str:
    if not job_id:
        raise PipelineActionError(
            code="job_id_required",
            detail="Include a job id to dismiss, e.g. `/dismiss jb_cat_001`.",
        )
    try:
        await dismiss_job_for_user(session, user_id, job_id)
    except LookupError:
        raise PipelineActionError(
            code="job_not_found",
            detail=f"Job `{job_id}` was not found.",
        ) from None

    return (
        "Summary:\n"
        f"- Dismissed job `{job_id}` from your Discover matches.\n"
        "Recommended Actions:\n"
        "- Refresh Discover to continue reviewing remaining roles.\n"
        "Why:\n"
        "- Dismissals hide roles from your feed without deleting catalog data.\n"
        "Next Step:\n"
        "- Review your next highest-fit match."
    )


async def pipeline_snapshot_action(*, session: AsyncSession, user_id: str) -> str:
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
        return (
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

    status_text = ", ".join(f"{k}:{v}" for k, v in sorted(status_counts.items()))
    recent_lines = [
        f"- {company} — {title} (status={status}, channel={channel})"
        for status, channel, company, title in recent_rows
    ]
    if not recent_lines:
        recent_lines = ["- No recent pipeline items found."]

    return (
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
