from datetime import datetime, timedelta, timezone

import pytest

from models.application import Application
from models.approval import Approval
from models.job import Job
from models.job_score import JobScore
from models.user import User
from services.dashboard_service import HIGH_FIT_THRESHOLD, get_dashboard_summary


@pytest.mark.asyncio
async def test_dashboard_summary_counts(db_session):
    uid = "user_dash_1"
    db_session.add(User(id=uid, email="dash@example.com"))
    jid = "job_dash_1"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="ext1",
            title="T",
            company="C",
            location="Remote",
            description="d",
            url="https://example.com/j",
        )
    )
    now = datetime.now(timezone.utc)
    db_session.add(
        JobScore(
            id="js1",
            user_id=uid,
            job_id=jid,
            fit_score=4.5,
            fit_reasons=[],
            risk_flags=[],
            dimension_scores={},
            scored_at=now,
        )
    )
    db_session.add(
        Application(
            id="app1",
            user_id=uid,
            job_id=jid,
            status="applied",
            channel="email",
        )
    )
    db_session.add(
        Approval(
            id="ap1",
            user_id=uid,
            application_id="app1",
            type="cover_letter",
            channel="email",
            subject="s",
            draft_body="x",
            status="pending",
        )
    )
    await db_session.commit()

    summary = await get_dashboard_summary(db_session, uid)
    assert summary.high_fit_count == 1
    assert summary.pipeline_count == 1
    assert summary.pending_approvals == 1
    assert summary.total_scored_jobs == 1
    assert summary.applied_awaiting_reply == 1
    assert summary.avg_fit_score == pytest.approx(4.5)
    assert summary.evaluated_this_week >= 1


@pytest.mark.asyncio
async def test_high_fit_threshold_boundary(db_session):
    uid = "user_dash_2"
    db_session.add(User(id=uid, email="dash2@example.com"))
    jid = "job_dash_2"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="ext2",
            title="T",
            company="C",
            location="Remote",
            description="d",
            url="https://example.com/j",
        )
    )
    db_session.add(
        JobScore(
            id="js_low",
            user_id=uid,
            job_id=jid,
            fit_score=float(HIGH_FIT_THRESHOLD) - 0.1,
            fit_reasons=[],
            risk_flags=[],
            dimension_scores={},
            scored_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    summary = await get_dashboard_summary(db_session, uid)
    assert summary.high_fit_count == 0
