"""LLM-backed draft creation for approvals (falls back to a template when LLM is unavailable)."""

from __future__ import annotations

import re
import json
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.application import Application
from models.approval import Approval
from models.job import Job
from models.job_score import JobScore as JobScoreRow
from models.resume import Resume
from schemas.approvals import Approval as ApprovalSchema
from services.approvals_service import build_approval_schema
from services.llm_prompts import draft_email_system, draft_linkedin_system
from services.openrouter import chat_completion


class DraftEnvelope(BaseModel):
    subject: str | None = None
    body: str
    used_fact_ids: list[str] = Field(default_factory=list)


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
    return await _llm_draft_with_profile_facts(job, channel, profile_facts=[])


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def _llm_draft_with_profile_facts(
    job: Job,
    channel: str,
    *,
    profile_facts: list[str],
) -> tuple[str, str | None]:
    desc = (job.description or "").strip()
    desc = desc[:6000]
    sys_msg = draft_linkedin_system() if channel == "linkedin" else draft_email_system()
    facts_block = "\n".join(
        f"F{i + 1}: {fact.strip()}" for i, fact in enumerate(profile_facts) if isinstance(fact, str) and fact.strip()
    )
    if not facts_block:
        facts_block = "None. Do not make personal claims about the candidate."
    fact_ids = {f"F{i + 1}" for i, _ in enumerate(profile_facts)}
    if channel == "linkedin":
        user_msg = (
            "Write a short LinkedIn outreach note (under 1200 characters, no subject line).\n"
            f"Role: {job.title}\nCompany: {job.company}\nLocation: {job.location or 'unspecified'}\n\n"
            f"PROFILE_FACTS:\n{facts_block}\n\n"
            f"Job description excerpt:\n{desc}\n"
        )
    else:
        user_msg = (
            "Write a professional email body for applying to this role.\n\n"
            f"Role: {job.title}\nCompany: {job.company}\nLocation: {job.location or 'unspecified'}\n\n"
            f"PROFILE_FACTS:\n{facts_block}\n\n"
            f"Job description excerpt:\n{desc}\n"
        )
    raw = await chat_completion(system_message=sys_msg, user_message=user_msg, use_case="drafts")
    try:
        envelope = DraftEnvelope.model_validate(_extract_json(raw))
    except (json.JSONDecodeError, ValidationError):
        return _fallback_draft(job, channel)
    if not envelope.body.strip():
        return _fallback_draft(job, channel)
    if fact_ids and (not envelope.used_fact_ids or not set(envelope.used_fact_ids).issubset(fact_ids)):
        return _fallback_draft(job, channel)
    if channel == "linkedin":
        return envelope.body.strip()[:4000], None
    subject = (envelope.subject or "").strip() or f"Application — {job.title} ({job.company})"
    return envelope.body.strip(), subject


def _profile_facts_from_resume(resume: Resume | None) -> list[str]:
    if resume is None or not isinstance(resume.parsed_profile, dict):
        return []
    profile = resume.parsed_profile
    facts: list[str] = []
    name = str(profile.get("name") or "").strip()
    headline = str(profile.get("headline") or "").strip()
    summary = str(profile.get("summary") or "").strip()
    exp = profile.get("experience_years")
    skills = profile.get("skills") if isinstance(profile.get("skills"), list) else []
    if name:
        facts.append(f"Candidate name: {name}")
    if headline:
        facts.append(f"Headline: {headline}")
    if isinstance(exp, (int, float)) and exp > 0:
        facts.append(f"Experience years: {exp}")
    if skills:
        facts.append("Skills: " + ", ".join(str(s).strip() for s in skills[:20] if str(s).strip()))
    if summary:
        facts.append("Summary: " + summary[:700])
    return facts[:12]


async def generate_draft_text(
    session: AsyncSession,
    user_id: str,
    job: Job,
    channel: str,
) -> tuple[str, str | None]:
    resume = (
        await session.execute(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc(), Resume.version.desc()).limit(1)
        )
    ).scalar_one_or_none()
    profile_facts = _profile_facts_from_resume(resume)
    if settings.openrouter_api_key:
        try:
            return await _llm_draft_with_profile_facts(job, channel, profile_facts=profile_facts)
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

    draft_body, subject = await generate_draft_text(session, user_id, job, app.channel)

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
