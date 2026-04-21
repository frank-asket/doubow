import pytest

from config import settings
from models.job import Job
from models.user import User
from services.jobs_service import dismiss_job_for_user, list_jobs
from services.semantic_match_service import SemanticMatcherUnavailableError

_SCORE_TEMPLATE = {
    "fit_score": 4.0,
    "fit_reasons": ["ok"],
    "risk_flags": [],
    "dimension_scores": {
        "tech": 4.0,
        "culture": 4.0,
        "seniority": 4.0,
        "comp": 4.0,
        "location": 4.0,
        "channel_recommendation": "email",
    },
}


@pytest.mark.asyncio
async def test_list_jobs_bootstraps_catalog_scores(db_session):
    db_session.add(User(id="user_jobs_1", email="jobs1@example.com"))
    for jid, ext_id, title, company, loc in (
        ("jb_cat_001", "cat-001", "Senior AI Product Engineer", "Northwind Labs", "Remote · EU"),
        ("jb_cat_002", "cat-002", "ML Platform Engineer", "Riverstone", "Berlin / Hybrid"),
    ):
        db_session.add(
            Job(
                id=jid,
                source="catalog",
                external_id=ext_id,
                title=title,
                company=company,
                location=loc,
                salary_range=None,
                description="Test",
                url=f"https://example.com/{jid}",
                score_template=_SCORE_TEMPLATE,
            )
        )
    await db_session.commit()

    res = await list_jobs(db_session, "user_jobs_1", min_fit=0.0, location=None, page=1, per_page=20)
    assert res.total == 2
    assert len(res.items) == 2
    titles = {j.title for j in res.items}
    assert "Senior AI Product Engineer" in titles
    assert "ML Platform Engineer" in titles


@pytest.mark.asyncio
async def test_dismiss_removes_score_and_blocks_rescore(db_session):
    db_session.add(User(id="user_jobs_2", email="jobs2@example.com"))
    jid = "jb_cat_099"
    db_session.add(
        Job(
            id=jid,
            source="catalog",
            external_id="cat-099",
            title="Dismissable role",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="x",
            url="https://example.com/x",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    res1 = await list_jobs(db_session, "user_jobs_2", 0.0, None, 1, 20)
    assert len(res1.items) == 1

    await dismiss_job_for_user(db_session, "user_jobs_2", jid)

    res2 = await list_jobs(db_session, "user_jobs_2", 0.0, None, 1, 20)
    assert res2.total == 0

    res3 = await list_jobs(db_session, "user_jobs_2", 0.0, None, 1, 20)
    assert res3.total == 0


@pytest.mark.asyncio
async def test_list_jobs_semantic_blend_enabled(db_session, monkeypatch):
    monkeypatch.setattr(settings, "use_semantic_matching", True)
    monkeypatch.setattr(settings, "semantic_matching_weight", 0.25)
    monkeypatch.setattr("services.jobs_service.semantic_fit_score", lambda profile, job: 5.0)

    db_session.add(User(id="user_jobs_sem_1", email="jobssem1@example.com"))
    db_session.add(
        Job(
            id="jb_cat_sem_1",
            source="catalog",
            external_id="cat-sem-1",
            title="Semantic Blend Role",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="Semantic test",
            url="https://example.com/sem-1",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    res = await list_jobs(db_session, "user_jobs_sem_1", min_fit=0.0, location=None, page=1, per_page=20)
    assert res.total == 1
    item = res.items[0]
    # Blend: 0.75 * 4.0 + 0.25 * 5.0 = 4.25 -> rounded to 4.2
    assert item.score.fit_score == 4.2
    assert any("Semantic similarity signal" in r for r in item.score.fit_reasons)


@pytest.mark.asyncio
async def test_list_jobs_semantic_unavailable_fallbacks(db_session, monkeypatch):
    monkeypatch.setattr(settings, "use_semantic_matching", True)
    monkeypatch.setattr(settings, "semantic_matching_weight", 0.25)

    def _boom(profile, job):  # type: ignore[no-untyped-def]
        raise SemanticMatcherUnavailableError("missing")

    monkeypatch.setattr("services.jobs_service.semantic_fit_score", _boom)

    db_session.add(User(id="user_jobs_sem_2", email="jobssem2@example.com"))
    db_session.add(
        Job(
            id="jb_cat_sem_2",
            source="catalog",
            external_id="cat-sem-2",
            title="Semantic Fallback Role",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="Semantic test",
            url="https://example.com/sem-2",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    res = await list_jobs(db_session, "user_jobs_sem_2", min_fit=0.0, location=None, page=1, per_page=20)
    assert res.total == 1
    item = res.items[0]
    assert item.score.fit_score == 4.0
    assert all("Semantic similarity signal" not in r for r in item.score.fit_reasons)
