import pytest

from config import settings
from models.job import Job
from models.job_score import JobScore
from models.resume import Resume
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


@pytest.mark.asyncio
async def test_list_jobs_lexical_overlap_blend_when_semantic_disabled(db_session, monkeypatch):
    monkeypatch.setattr(settings, "use_semantic_matching", False)
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.5)

    db_session.add(User(id="user_jobs_lex_1", email="jobslex1@example.com"))
    db_session.add(
        Job(
            id="jb_cat_lex_1",
            source="catalog",
            external_id="cat-lex-1",
            title="Senior AI Product Engineer",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="Build ML platform and LLM features",
            url="https://example.com/lex-1",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    db_session.add(
        Resume(
            user_id="user_jobs_lex_1",
            file_name="resume.pdf",
            storage_path="/tmp/resume.pdf",
            version=1,
            parsed_profile={
                "headline": "School Administrator",
                "summary": "Led student operations, parent communication, policy compliance.",
                "skills": ["curriculum", "administration", "operations", "communication"],
            },
            preferences={},
        )
    )
    await db_session.commit()

    res = await list_jobs(db_session, "user_jobs_lex_1", min_fit=0.0, location=None, page=1, per_page=20)
    assert res.total == 1
    item = res.items[0]
    assert item.score.fit_score < 4.0
    assert any("Keyword overlap signal" in r for r in item.score.fit_reasons)


@pytest.mark.asyncio
async def test_recompute_scores_force_refreshes_existing_rows(db_session, monkeypatch):
    from services.jobs_service import recompute_job_scores_for_user

    monkeypatch.setattr(settings, "use_semantic_matching", False)
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.5)

    uid = "user_jobs_recompute_1"
    db_session.add(User(id=uid, email="recompute1@example.com"))
    db_session.add(
        Resume(
            user_id=uid,
            file_name="resume.pdf",
            storage_path="/tmp/resume.pdf",
            version=1,
            parsed_profile={
                "headline": "School Administrator",
                "summary": "student operations curriculum admissions compliance",
                "skills": ["curriculum", "administration", "operations"],
            },
            preferences={},
        )
    )
    db_session.add(
        Job(
            id="jb_cat_recompute_1",
            source="catalog",
            external_id="cat-recompute-1",
            title="Senior AI Product Engineer",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="Build ML platform and LLM features",
            url="https://example.com/recompute-1",
            score_template=_SCORE_TEMPLATE,
        )
    )
    db_session.add(
        JobScore(
            id="score_old_1",
            user_id=uid,
            job_id="jb_cat_recompute_1",
            fit_score=4.0,
            fit_reasons=["stale"],
            risk_flags=[],
            dimension_scores=_SCORE_TEMPLATE["dimension_scores"],
        )
    )
    await db_session.commit()

    refreshed = await recompute_job_scores_for_user(db_session, uid)
    assert refreshed == 1

    res = await list_jobs(db_session, uid, min_fit=0.0, location=None, page=1, per_page=20)
    assert res.total == 1
    item = res.items[0]
    assert item.score.fit_score < 4.0
    assert any("Keyword overlap signal" in r for r in item.score.fit_reasons)


@pytest.mark.asyncio
async def test_list_jobs_llm_matching_applies_only_top_n(db_session, monkeypatch):
    monkeypatch.setattr(settings, "use_semantic_matching", False)
    monkeypatch.setattr(settings, "lexical_matching_weight", 0.0)
    monkeypatch.setattr(settings, "use_llm_job_matching", True)
    monkeypatch.setattr(settings, "llm_job_matching_weight", 0.5)
    monkeypatch.setattr(settings, "llm_job_matching_top_n", 2)
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")

    uid = "user_jobs_llm_top_n"
    db_session.add(User(id=uid, email="llm-top-n@example.com"))
    for idx, fit in enumerate((4.9, 4.5, 4.0), start=1):
        db_session.add(
            Job(
                id=f"jb_cat_llm_{idx}",
                source="catalog",
                external_id=f"cat-llm-{idx}",
                title=f"LLM Role {idx}",
                company="Acme",
                location="Remote",
                salary_range=None,
                description="Test description",
                url=f"https://example.com/llm-{idx}",
                score_template={
                    **_SCORE_TEMPLATE,
                    "fit_score": fit,
                },
            )
        )
    await db_session.commit()

    called_job_ids: list[str] = []

    async def _fake_llm_fit_signal(_profile, job):  # type: ignore[no-untyped-def]
        called_job_ids.append(job.id)
        return 5.0, ["strong alignment"], []

    monkeypatch.setattr("services.jobs_service.llm_fit_signal", _fake_llm_fit_signal)

    res = await list_jobs(db_session, uid, min_fit=0.0, location=None, page=1, per_page=20)
    assert res.total == 3

    # Only the top-2 baseline jobs should invoke LLM matching.
    assert set(called_job_ids) == {"jb_cat_llm_1", "jb_cat_llm_2"}
    assert len(called_job_ids) == 2

    by_id = {item.id: item for item in res.items}
    # Top-N got LLM blended upward.
    assert by_id["jb_cat_llm_1"].score.fit_score == 5.0
    assert by_id["jb_cat_llm_2"].score.fit_score == 4.8
    # Outside top-N remains baseline template score.
    assert by_id["jb_cat_llm_3"].score.fit_score == 4.0


@pytest.mark.asyncio
async def test_list_jobs_has_salary_filter_returns_only_salary_rows(db_session):
    uid = "user_jobs_salary_filter"
    db_session.add(User(id=uid, email="salary-filter@example.com"))
    db_session.add(
        Job(
            id="jb_salary_yes",
            source="catalog",
            external_id="salary-yes",
            title="Comp-Visible Role",
            company="Acme",
            location="Remote",
            salary_range="$120k-$150k",
            description="Paid role",
            url="https://example.com/salary-yes",
            score_template=_SCORE_TEMPLATE,
        )
    )
    db_session.add(
        Job(
            id="jb_salary_no",
            source="catalog",
            external_id="salary-no",
            title="No-Comp Role",
            company="Acme",
            location="Remote",
            salary_range=None,
            description="No salary",
            url="https://example.com/salary-no",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    unfiltered = await list_jobs(db_session, uid, min_fit=0.0, location=None, has_salary=False, page=1, per_page=20)
    assert unfiltered.total == 2

    filtered = await list_jobs(db_session, uid, min_fit=0.0, location=None, has_salary=True, page=1, per_page=20)
    assert filtered.total == 1
    assert len(filtered.items) == 1
    assert filtered.items[0].id == "jb_salary_yes"


@pytest.mark.asyncio
async def test_list_jobs_location_filter_matches_normalized_tokens(db_session):
    uid = "user_jobs_location_filter"
    db_session.add(User(id=uid, email="location-filter@example.com"))
    db_session.add(
        Job(
            id="jb_loc_accra",
            source="catalog",
            external_id="loc-accra",
            title="Accra Role",
            company="Acme",
            location="Accra - Greater Accra Region, Ghana",
            salary_range=None,
            description="Location matching test",
            url="https://example.com/loc-accra",
            score_template=_SCORE_TEMPLATE,
        )
    )
    db_session.add(
        Job(
            id="jb_loc_berlin",
            source="catalog",
            external_id="loc-berlin",
            title="Berlin Role",
            company="Acme",
            location="Berlin, Germany",
            salary_range=None,
            description="Location matching test",
            url="https://example.com/loc-berlin",
            score_template=_SCORE_TEMPLATE,
        )
    )
    await db_session.commit()

    filtered = await list_jobs(db_session, uid, min_fit=0.0, location="Accra, Ghana", page=1, per_page=20)
    assert filtered.total == 1
    assert len(filtered.items) == 1
    assert filtered.items[0].id == "jb_loc_accra"
