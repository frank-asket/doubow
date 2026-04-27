"""Generate interview prep content (questions, STAR stories, company brief) via LLM or template."""

from __future__ import annotations

import json
import logging
import re
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from config import settings
from models.job import Job
from services.llm_prompts import prep_json_only_system
from services.openrouter import chat_completion

logger = logging.getLogger(__name__)


class StarStoryStructured(BaseModel):
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    reflection: str = ""
    tags: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


class PrepStructured(BaseModel):
    questions: list[str] = Field(default_factory=list)
    star_stories: list[StarStoryStructured] = Field(default_factory=list)
    company_brief: str = ""


def _extract_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _fallback_prep(job: Job) -> PrepStructured:
    company = job.company.strip() or "the company"
    title = job.title.strip() or "this role"
    return PrepStructured(
        questions=[
            f"What draws you to {company} specifically for the {title} role?",
            "Walk through a technical decision you owned end-to-end.",
            "Describe how you collaborate with stakeholders when priorities conflict.",
            "Tell me about a production incident or bug you diagnosed and resolved.",
            "Where do you want to grow in the next 12 months?",
        ],
        star_stories=[
            StarStoryStructured(
                situation=f"Mid-size team shipping customer-facing features at pace; reliability expectations rising.",
                task=f"Lead delivery of a critical initiative aligned with {title} responsibilities.",
                action="Defined milestones, coordinated cross-functional reviews, and instrumented rollout with metrics.",
                result="Shipped on schedule with measurable quality improvement post-launch.",
                reflection="Earlier alignment on scope with stakeholders would have reduced rework.",
                tags=["delivery", "collaboration"],
                confidence="medium",
            )
        ],
        company_brief=(
            f"{company} — template brief. Configure OPENROUTER_API_KEY for AI-generated research from the job posting."
        ),
    )


def _infer_story_confidence(story: StarStoryStructured) -> Literal["low", "medium", "high"]:
    parts = [story.situation, story.task, story.action, story.result]
    shortest = min((len((p or "").strip()) for p in parts), default=0)
    total = sum(len((p or "").strip()) for p in parts)
    has_metric = bool(re.search(r"\b\d+([.,]\d+)?\b", (story.result or "") + " " + (story.action or "")))
    if shortest < 24 or total < 180:
        return "low"
    if has_metric and total >= 320 and len((story.action or "").strip()) >= 80:
        return "high"
    return "medium"


async def generate_prep_structured(job: Job) -> PrepStructured:
    posting = (job.description or "").strip()[:8000]
    sys_msg = prep_json_only_system()
    user_msg = (
        "Produce interview prep as JSON with keys: questions (array of 5 strings), "
        "star_stories (array of up to 2 objects with keys situation, task, action, result, reflection, tags, confidence), "
        "company_brief (string, 2-4 sentences about the employer inferred from the posting).\n\n"
        f"Role: {job.title}\nCompany: {job.company}\nLocation: {job.location or 'unspecified'}\n\n"
        f"Job posting:\n{posting}"
    )

    if settings.openrouter_api_key:
        try:
            raw = await chat_completion(system_message=sys_msg, user_message=user_msg, use_case="prep")
            data = _extract_json_object(raw)
            structured = PrepStructured.model_validate(data)
            for story in structured.star_stories:
                # Enforce deterministic confidence classification from content quality.
                story.confidence = _infer_story_confidence(story)
            if not structured.questions:
                structured = _fallback_prep(job)
            return structured
        except Exception:
            logger.exception("prep LLM generation failed; using template")

    return _fallback_prep(job)


def prep_structured_to_storage_dict(structured: PrepStructured, job: Job) -> tuple[list[str], list[dict], str]:
    questions = [q.strip() for q in structured.questions if isinstance(q, str) and q.strip()][:12]
    stories: list[dict] = []
    for s in structured.star_stories[:4]:
        stories.append(
            {
                "situation": s.situation.strip(),
                "task": s.task.strip(),
                "action": s.action.strip(),
                "result": s.result.strip(),
                "reflection": s.reflection.strip(),
                "tags": [str(t).strip() for t in (s.tags or []) if str(t).strip()][:12],
                "confidence": s.confidence,
            }
        )
    brief = structured.company_brief.strip() or (
        f"{job.company.strip() or 'The company'} — add OPENROUTER_API_KEY for an AI-generated company brief."
    )
    return questions, stories, brief


def new_prep_session_id() -> str:
    return f"prep_{uuid4().hex[:12]}"
