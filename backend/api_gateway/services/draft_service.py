"""LLM-backed draft creation for approvals (falls back to a template when LLM is unavailable)."""

from __future__ import annotations

import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.application import Application
from models.approval import Approval
from models.job import Job
from models.job_score import JobScore as JobScoreRow
from schemas.approvals import Approval as ApprovalSchema
from services.approvals_service import build_approval_schema
from services.openrouter import chat_completion


def _channel_to_approval_type(channel: str) -> str:
    if channel == "linkedin":
        return "linkedin_note"
    return "cover_letter"


def _fallback_draft(job: Job, channel: str) -> tuple[str, str | None]:
    company = job.company.strip() or "your team"
    title = job.title.strip() or "this role"
    if channel == "linkedin":
        body = (
            f"Hi — I applied for the {title} role at {company}. "
            f"I'm excited about the work and would welcome a conversation. "
            f"(Configure OPENROUTER_API_KEY for a tailored draft.)"
        )
        return body, None
    body = (
        f"Dear Hiring Team,\n\n"
        f"I am writing to express my interest in the {title} position at {company}.\n\n"
        f"My background aligns with what you're building; I'd welcome the chance to discuss how I can contribute.\n\n"
        f"(Configure OPENROUTER_API_KEY for an AI-tailored draft from your profile and this posting.)\n\n"
        f"Best regards"
    )
    subject = f"Application — {title} ({company})"
    return body, subject


async def _llm_draft(job: Job, channel: str) -> tuple[str, str | None]:
    desc = (job.description or "").strip()
    desc = desc[:6000]
    sys_msg = (
        "You write concise, professional outbound messages for job applications. "
        "Follow the user's channel constraints exactly."
    )
    if channel == "linkedin":
        user_msg = (
            f"Write a short LinkedIn outreach note (under 1200 characters, no subject line).\n"
            f"Role: {job.title}\nCompany: {job.company}\nLocation: {job.location or 'unspecified'}\n\n"
            f"Job description excerpt:\n{desc}\n"
        )
    else:
        user_msg = (
            f"Write a professional email body for applying to this role. "
            f"Also output SUBJECT: on its own line first, then the body.\n\n"
            f"Role: {job.title}\nCompany: {job.company}\nLocation: {job.location or 'unspecified'}\n\n"
            f"Job description excerpt:\n{desc}\n"
        )
    raw = await chat_completion(system_message=sys_msg, user_message=user_msg)
    raw = raw.strip()
    if channel == "linkedin":
        return raw[:4000], None

    subject: str | None = None
    body = raw
    m = re.match(r"^SUBJECT:\s*(.+)$", raw, flags=re.MULTILINE)
    if m:
        subject = m.group(1).strip()
        body = raw[m.end() :].strip()
    if not body:
        return _fallback_draft(job, channel)
    return body, subject or f"Application — {job.title} ({job.company})"


async def generate_draft_text(job: Job, channel: str) -> tuple[str, str | None]:
    if settings.openrouter_api_key:
        try:
            return await _llm_draft(job, channel)
        except Exception:
            pass
    return _fallback_draft(job, channel)


class ApplicationNotFoundError(LookupError):
    pass


async def create_draft_approval_for_application(
    session: AsyncSession, user_id: str, application_id: str
) -> ApprovalSchema:
    stmt = (
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(Application.id == application_id, Application.user_id == user_id)
    )
    row = (await session.execute(stmt)).one_or_none()
    if row is None:
        raise ApplicationNotFoundError(application_id)

    app, job = row

    pending = (
        await session.execute(
            select(Approval).where(Approval.application_id == app.id, Approval.status == "pending")
        )
    ).scalar_one_or_none()
    if pending is not None:
        score_row = (
            await session.execute(
                select(JobScoreRow).where(JobScoreRow.user_id == user_id, JobScoreRow.job_id == job.id)
            )
        ).scalar_one_or_none()
        return build_approval_schema(pending, app, job, score_row)

    score_row = (
        await session.execute(
            select(JobScoreRow).where(JobScoreRow.user_id == user_id, JobScoreRow.job_id == job.id)
        )
    ).scalar_one_or_none()

    draft_body, subject = await generate_draft_text(job, app.channel)

    approval = Approval(
        id=f"apr_{uuid4().hex[:12]}",
        user_id=user_id,
        application_id=app.id,
        type=_channel_to_approval_type(app.channel),
        channel=app.channel,
        subject=subject,
        draft_body=draft_body,
        status="pending",
    )
    session.add(approval)
    await session.commit()
    await session.refresh(approval)

    return build_approval_schema(approval, app, job, score_row)
