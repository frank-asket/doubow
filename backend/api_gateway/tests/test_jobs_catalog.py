import pytest

from models.job import Job
from models.user import User
from services.jobs_service import dismiss_job_for_user, list_jobs

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
