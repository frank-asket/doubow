"""Prep session generation persists rows and returns nested application payloads."""

import json

import pytest

from models.application import Application
from models.job import Job
from models.user import User
from services.prep_assist_service import generate_prep_assist_text
from services.prep_service import PrepApplicationNotFoundError, generate_prep_for_application, get_prep_detail_for_user
from services import prep_generation


@pytest.mark.asyncio
async def test_prep_structured_fills_fallback_star_when_llm_returns_questions_only(monkeypatch):
    """Regression: partial LLM JSON (questions but no STAR blocks) must still persist STAR content."""

    async def _fake_chat_completion(**_kwargs):
        return json.dumps(
            {
                "questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
                "star_stories": [],
                "company_brief": "Short brief.",
            }
        )

    monkeypatch.setattr(prep_generation.settings, "openrouter_api_key", "sk-test-key")
    monkeypatch.setattr(prep_generation, "chat_completion", _fake_chat_completion)

    job = Job(
        id="job_star_fallback",
        source="manual",
        external_id="star-fb",
        title="Backend Engineer",
        company="Acme",
        location="Remote",
        description="Build APIs",
        url="https://example.com/job",
    )
    structured = await prep_generation.generate_prep_structured(job)
    assert structured.questions == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert len(structured.star_stories) >= 1
    assert structured.star_stories[0].confidence in {"low", "medium", "high"}


@pytest.mark.asyncio
async def test_generate_prep_creates_session_and_get_returns_detail(db_session, monkeypatch):
    """Avoid real OpenRouter calls: same env may have a key, and live models can omit `star_stories`."""

    async def _fake_chat_completion(**_kwargs):
        return json.dumps(
            {
                "questions": [f"Interview question {i + 1}?" for i in range(5)],
                "star_stories": [
                    {
                        "situation": "Mid-size team shipping customer-facing features; reliability expectations were rising quarter over quarter.",
                        "task": "Lead delivery of a critical initiative aligned with Backend Engineer responsibilities for the platform team.",
                        "action": "Defined milestones, coordinated cross-functional reviews, and instrumented the rollout with metrics and dashboards.",
                        "result": "Shipped on schedule with a 40% drop in p99 latency and strong stakeholder sign-off after launch.",
                        "reflection": "Earlier scope alignment with stakeholders would have reduced rework in the final sprint.",
                        "tags": ["delivery", "reliability"],
                        "confidence": "medium",
                    }
                ],
                "company_brief": "Acme Labs — builds APIs and platform services for internal and external customers.",
            }
        )

    monkeypatch.setattr(prep_generation.settings, "openrouter_api_key", "sk-test-key")
    monkeypatch.setattr(prep_generation, "chat_completion", _fake_chat_completion)

    uid = "user_prep_gen"
    db_session.add(User(id=uid, email="prep@example.com"))
    jid = "job_prep_gen"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="prep-j",
            title="Backend Engineer",
            company="Acme Labs",
            location="Remote",
            description="Build APIs",
            url="https://example.com/job",
        )
    )
    await db_session.commit()
    aid = "app_prep_gen"
    db_session.add(Application(id=aid, user_id=uid, job_id=jid, status="pending", channel="email"))
    await db_session.commit()

    detail = await generate_prep_for_application(db_session, uid, aid)
    assert detail.id.startswith("prep_")
    assert detail.application.id == aid
    assert len(detail.questions) >= 1
    assert detail.company_brief
    assert detail.star_stories
    assert detail.star_stories[0].get("confidence") in {"low", "medium", "high"}

    loaded = await get_prep_detail_for_user(db_session, uid, aid)
    assert loaded is not None
    assert loaded.id == detail.id


@pytest.mark.asyncio
async def test_prep_assist_unknown_application_raises(db_session):
    uid = "user_prep_assist_missing"
    db_session.add(User(id=uid, email="miss@example.com"))
    await db_session.commit()

    with pytest.raises(PrepApplicationNotFoundError):
        await generate_prep_assist_text(db_session, uid, "app_does_not_exist", "company_brief")
