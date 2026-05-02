"""Multi-stage job search pipeline coordinator."""

import pytest
from sqlalchemy import select

from config import settings
from models.application import Application
from models.job import Job
from models.resume import Resume
from models.user import User
from schemas.job_search_pipeline import JobSearchPipelineRunRequest, JobSearchPipelineStageId
from services.job_search_pipeline import JobSearchPipelineCoordinator


@pytest.mark.asyncio
async def test_pipeline_resume_and_feedback_stages(db_session):
    uid = "user_pipeline_1"
    db_session.add(User(id=uid, email="p@example.com"))
    jid = "job_p1"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="x",
            title="Role",
            company="Co",
            location="Remote",
            description="desc",
            url="https://example.com",
        )
    )
    db_session.add(
        Resume(
            user_id=uid,
            file_name="cv.pdf",
            storage_path="/tmp/p",
            parsed_profile={"headline": "Engineer", "top_skills": ["Python"]},
            preferences={"target_role": "Backend", "location": "London"},
        )
    )
    db_session.add(
        Application(id="app_p1", user_id=uid, job_id=jid, status="applied", channel="email"),
    )
    await db_session.commit()

    coord = JobSearchPipelineCoordinator()
    res = await coord.run(
        db_session,
        settings=settings,
        user_id=uid,
        body=JobSearchPipelineRunRequest(
            stages=[JobSearchPipelineStageId.resume_profile, JobSearchPipelineStageId.feedback],
            trigger_catalog_refresh=False,
        ),
    )
    assert res.trace_id
    assert res.user_id == uid
    assert len(res.stages) == 2
    assert res.stages[0].stage == JobSearchPipelineStageId.resume_profile
    assert res.stages[0].ok is True
    assert res.stages[1].detail.get("applications_by_status", {}).get("applied") == 1
    fl = res.stages[1].detail.get("feedback_learning") or {}
    assert fl.get("version") == 1
    assert "matching_blend_hints" in fl


@pytest.mark.asyncio
async def test_data_collection_plan_without_refresh(db_session):
    uid = "user_pipeline_2"
    db_session.add(User(id=uid, email="p2@example.com"))
    await db_session.commit()

    coord = JobSearchPipelineCoordinator()
    res = await coord.run(
        db_session,
        settings=settings,
        user_id=uid,
        body=JobSearchPipelineRunRequest(stages=[JobSearchPipelineStageId.data_collection]),
    )
    assert res.stages[0].ok is True
    assert "readiness" in res.stages[0].detail


@pytest.mark.asyncio
async def test_feedback_persist_merges_preferences(db_session):
    uid = "user_pipeline_persist"
    db_session.add(User(id=uid, email="persist@example.com"))
    jid = "job_pp1"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="x",
            title="Role",
            company="Co",
            location="Remote",
            description="desc",
            url="https://example.com",
        )
    )
    db_session.add(
        Resume(
            user_id=uid,
            file_name="cv.pdf",
            storage_path="/tmp/p",
            parsed_profile={"headline": "Engineer"},
            preferences={"target_role": "Backend", "location": "London"},
        )
    )
    db_session.add(Application(id="app_pp1", user_id=uid, job_id=jid, status="applied", channel="email"))
    await db_session.commit()

    coord = JobSearchPipelineCoordinator()
    res = await coord.run(
        db_session,
        settings=settings,
        user_id=uid,
        body=JobSearchPipelineRunRequest(
            stages=[JobSearchPipelineStageId.feedback],
            persist_feedback_learning=True,
        ),
    )
    assert res.stages[0].ok is True
    d = res.stages[0].detail.get("persist_feedback_learning") or {}
    assert d.get("ok") is True

    row = (await db_session.execute(select(Resume).where(Resume.user_id == uid))).scalars().first()
    assert row is not None
    prefs = row.preferences or {}
    assert prefs.get("target_role") == "Backend"
    fl = prefs.get("feedback_learning") or {}
    assert fl.get("version") == 1
    assert fl.get("counts", {}).get("applied") == 1
