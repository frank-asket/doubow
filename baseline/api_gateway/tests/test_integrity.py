from datetime import datetime, timezone

from models.application import Application
from models.job import Job
import pytest
from services.applications_service import integrity_check


@pytest.mark.asyncio
async def test_integrity_dry_run_reports_dupes_and_stale(db_session):
    job = Job(
        id="job_int_1",
        source="manual",
        external_id="int-1",
        title="Backend Engineer",
        company="Doubow",
        location="Remote",
        description="",
        url="https://doubow.ai/jobs/int-1",
    )
    db_session.add(job)
    db_session.add_all(
        [
            Application(
                id="app_int_1",
                user_id="user_int",
                job_id="job_int_1",
                status="saved",
                channel="email",
                is_stale=True,
                dedup_group="group_1",
                last_updated=datetime.now(timezone.utc),
            ),
            Application(
                id="app_int_2",
                user_id="user_int",
                job_id="job_int_1",
                status="pending",
                channel="email",
                is_stale=False,
                dedup_group="group_1",
                last_updated=datetime.now(timezone.utc),
            ),
        ]
    )
    await db_session.commit()

    result = await integrity_check(session=db_session, user_id="user_int", mode="dry_run")
    assert result.summary.duplicates == 2
    assert result.summary.stale == 1
    assert len(result.changes) == 2
    assert {c.type for c in result.changes} == {"deduplicate", "mark_stale"}


@pytest.mark.asyncio
async def test_integrity_apply_clears_flags(db_session):
    job = Job(
        id="job_int_2",
        source="manual",
        external_id="int-2",
        title="Product Engineer",
        company="Doubow",
        location="Remote",
        description="",
        url="https://doubow.ai/jobs/int-2",
    )
    app = Application(
        id="app_int_3",
        user_id="user_apply",
        job_id="job_int_2",
        status="saved",
        channel="linkedin",
        is_stale=True,
        dedup_group="dup_apply",
        last_updated=datetime.now(timezone.utc),
    )
    db_session.add_all([job, app])
    await db_session.commit()

    result = await integrity_check(session=db_session, user_id="user_apply", mode="apply")
    assert result.mode == "apply"
    assert result.summary.duplicates == 1
    assert result.summary.stale == 1

    await db_session.refresh(app)
    assert app.is_stale is False
    assert app.dedup_group is None
