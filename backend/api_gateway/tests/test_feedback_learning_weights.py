"""Per-user matching blend from feedback_learning + preference helpers."""

import pytest
from sqlalchemy import select

from config import settings
from models.job import Job
from models.job_score import JobScore
from models.resume import Resume
from models.user import User
from services.jobs_service import (
    effective_matching_weights_from_preferences,
    matching_blend_preview_is_personalized,
    matching_blend_weight_preview,
    recompute_job_scores_for_user,
)
from services.resume_service import clear_feedback_learning_for_user, get_feedback_learning_debug_for_user


@pytest.fixture
def monkeypatch_lexical_only(monkeypatch):
    monkeypatch.setattr(settings, "use_semantic_matching", False)
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.5)
    monkeypatch.setattr(settings, "use_llm_job_matching", False)


def test_effective_matching_weights_applies_lexical_delta(monkeypatch):
    monkeypatch.setattr(settings, "semantic_matching_weight", 0.4)
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.5)
    monkeypatch.setattr(settings, "llm_job_matching_weight", 0.3)
    prefs = {"feedback_learning": {"matching_blend_hints": {"lexical_matching_delta": 0.1}}}
    sem, lex, llm = effective_matching_weights_from_preferences(prefs)
    assert lex == pytest.approx(0.6)
    assert sem == pytest.approx(0.4)
    assert llm == pytest.approx(0.3)


def test_matching_blend_preview(monkeypatch):
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.4)
    prefs = {"feedback_learning": {"matching_blend_hints": {"lexical_matching_delta": -0.05}}}
    prev = matching_blend_weight_preview(prefs)
    assert prev["effective"]["lexical"] == pytest.approx(0.35)


def test_matching_blend_preview_is_personalized_true(monkeypatch):
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.5)
    prev = matching_blend_weight_preview(
        {"feedback_learning": {"matching_blend_hints": {"lexical_matching_delta": 0.1}}}
    )
    assert matching_blend_preview_is_personalized(prev) is True


def test_matching_blend_preview_is_personalized_false(monkeypatch):
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.5)
    prev = matching_blend_weight_preview({})
    assert matching_blend_preview_is_personalized(prev) is False


_SCORE_TEMPLATE = {
    "fit_score": 4.0,
    "fit_reasons": ["ok"],
    "risk_flags": [],
    "dimension_scores": {"tech": 4.0, "culture": 4.0, "seniority": 4.0, "comp": 4.0, "location": 4.0},
}


@pytest.mark.asyncio
async def test_recompute_uses_lexical_hint_delta(db_session, monkeypatch_lexical_only):
    """Higher lexical weight from hints should change blended keyword score vs baseline."""
    jid = "jb_blend_hint_1"
    db_session.add(User(id="user_blend_base", email="b1@example.com"))
    db_session.add(User(id="user_blend_hint", email="h1@example.com"))
    for uid, prefs in (
        ("user_blend_base", {}),
        (
            "user_blend_hint",
            {
                "feedback_learning": {
                    "matching_blend_hints": {"lexical_matching_delta": 0.12},
                }
            },
        ),
    ):
        db_session.add(
            Resume(
                user_id=uid,
                file_name="cv.pdf",
                storage_path="/tmp/cv.pdf",
                version=1,
                parsed_profile={
                    "headline": "School Administrator",
                    "summary": "student operations curriculum admissions compliance",
                    "skills": ["curriculum", "administration"],
                },
                preferences=prefs,
            )
        )
    db_session.add(
        Job(
            id=jid,
            source="catalog",
            external_id="blend-1",
            title="Senior AI Product Engineer",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="Build ML platform",
            url="https://example.com/blend",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    await recompute_job_scores_for_user(db_session, "user_blend_base")
    await recompute_job_scores_for_user(db_session, "user_blend_hint")

    b = (
        await db_session.execute(select(JobScore.fit_score).where(JobScore.user_id == "user_blend_base", JobScore.job_id == jid))
    ).scalar_one()
    h = (
        await db_session.execute(select(JobScore.fit_score).where(JobScore.user_id == "user_blend_hint", JobScore.job_id == jid))
    ).scalar_one()
    assert b != h


@pytest.mark.asyncio
async def test_get_and_clear_feedback_learning_debug(db_session):
    uid = "user_fl_debug"
    db_session.add(User(id=uid, email="fd@example.com"))
    db_session.add(
        Resume(
            user_id=uid,
            file_name="cv.pdf",
            storage_path="/tmp/x.pdf",
            version=1,
            parsed_profile={"headline": "Dev"},
            preferences={
                "feedback_learning": {
                    "version": 1,
                    "matching_blend_hints": {"lexical_matching_delta": 0.05},
                }
            },
        )
    )
    await db_session.commit()

    fl, preview = await get_feedback_learning_debug_for_user(db_session, uid)
    assert fl is not None
    assert fl.get("version") == 1
    assert "effective" in preview

    await clear_feedback_learning_for_user(db_session, uid)
    row = (await db_session.execute(select(Resume).where(Resume.user_id == uid))).scalars().first()
    assert row is not None
    assert row.preferences.get("feedback_learning") is None


@pytest.mark.asyncio
async def test_recompute_observes_matching_blend_metric(db_session, monkeypatch_lexical_only, monkeypatch):
    import services.jobs_service as jobs_mod

    calls: list[dict] = []

    def capture(**kwargs: object) -> None:
        calls.append(dict(kwargs))

    monkeypatch.setattr(jobs_mod, "observe_matching_blend_score_sync", capture)

    jid = "jb_metric_blend"
    uid = "user_metric_blend"
    db_session.add(User(id=uid, email="mb@example.com"))
    db_session.add(
        Resume(
            user_id=uid,
            file_name="cv.pdf",
            storage_path="/tmp/cv.pdf",
            version=1,
            parsed_profile={"headline": "X", "skills": ["a"]},
            preferences={},
        )
    )
    db_session.add(
        Job(
            id=jid,
            source="catalog",
            external_id="m1",
            title="Role",
            company="Co",
            location="Remote",
            salary_range=None,
            description="Text",
            url="https://example.com/m",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    await recompute_job_scores_for_user(db_session, uid)
    assert len(calls) == 1
    assert calls[0]["has_feedback_learning"] is False
    assert calls[0]["personalized_blend"] is False
