"""LLM-assisted prep snippets (company brief, STAR story) via OpenRouter — never call model APIs from the browser."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from services.openrouter import chat_completion
from services.prep_service import fetch_application_job_for_user


async def generate_prep_assist_text(
    session: AsyncSession,
    user_id: str,
    application_id: str,
    kind: str,
) -> str:
    _app, job, _score = await fetch_application_job_for_user(session, user_id, application_id)

    if kind == "company_brief":
        system = (
            "You are Doubow. Write a concise company brief for interview preparation. "
            "Be professional and avoid inventing facts — infer only from general public knowledge about the company name and role title."
        )
        user = (
            f"Company brief for {job.company} — {job.title}.\n"
            "Cover: (1) what the company likely does and positioning, (2) tech/product signals from the role title and any description hints, "
            "(3) culture/engineering values as reasonable assumptions, (4) 2 smart questions to ask interviewers.\n"
            f"Job description excerpt (may be short):\n{(job.description or '').strip()[:4000]}"
        )
    elif kind == "star_story":
        system = (
            "You are Doubow, an AI job search assistant. Generate one specific, concrete STAR-R interview story. "
            "Be precise; use plausible metrics. Format with clear section labels: Situation, Task, Action, Result, Reflection."
        )
        user = (
            f"Generate a STAR-R story for an engineer interviewing at {job.company} for {job.title}. "
            "Demonstrate shipping production impact. Include quantitative results where reasonable.\n"
            f"Role context:\n{(job.description or '').strip()[:3000]}"
        )
    else:
        raise ValueError(f"unknown assist kind: {kind!r}")

    return await chat_completion(system_message=system, user_message=user)
