from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from models.job import Job
from models.job_score import JobScore
from models.telemetry_event import TelemetryEvent
from models.user import User
from routers import jobs as jobs_router_module
from schemas.jobs import (
    CareerOpsScanHistoryResponse,
    CareerOpsScanRunRequest,
    CareerOpsScanRunResponse,
)
from services.career_ops_scan_service import list_career_ops_scan_runs, run_career_ops_scan


@pytest.mark.asyncio
async def test_run_career_ops_scan_success_records_counts_and_events(db_session):
    user_id = "career_ops_user_1"
    db_session.add(User(id=user_id, email="careerops1@example.com"))
    db_session.add(
        Job(
            id="job_cos_1",
            source="manual",
            external_id="cos-ext-1",
            title="Platform Engineer",
            company="Acme",
            location="Remote",
            description="Role one",
            url="https://example.com/jobs/1",
        )
    )
    db_session.add(
        Job(
            id="job_cos_2",
            source="manual",
            external_id="cos-ext-2",
            title="Backend Engineer",
            company="Beta",
            location="Remote",
            description="Role two",
            url="https://example.com/jobs/2",
        )
    )
    db_session.add(
        JobScore(
            user_id=user_id,
            job_id="job_cos_1",
            fit_score=4.6,
            fit_reasons=["strong fit"],
            risk_flags=[],
            dimension_scores={"tech": 4.5, "culture": 4.2, "seniority": 4.7, "comp": 4.1, "location": 5.0},
            scored_at=datetime.now(UTC),
        )
    )
    db_session.add(
        JobScore(
            user_id=user_id,
            job_id="job_cos_2",
            fit_score=3.2,
            fit_reasons=["partial fit"],
            risk_flags=[],
            dimension_scores={"tech": 3.0, "culture": 3.5, "seniority": 3.0, "comp": 3.3, "location": 4.0},
            scored_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    payload = CareerOpsScanRunRequest(
        min_fit_threshold=4.0,
        queue_top_n=2,
        trigger_catalog_refresh=False,
    )
    response = await run_career_ops_scan(session=db_session, user_id=user_id, payload=payload)

    assert response.status == "done"
    assert response.scored >= 0
    assert response.kept_after_threshold == 1
    assert response.queued_to_pipeline == 1
    assert response.top_job_ids == ["job_cos_1"]

    telemetry_names = (
        await db_session.execute(
            select(TelemetryEvent.event_name).where(TelemetryEvent.user_id == user_id)
        )
    ).scalars().all()
    assert "career_ops_scan_started" in telemetry_names
    assert "career_ops_threshold_applied" in telemetry_names
    assert "career_ops_queue_top_n_clicked" in telemetry_names
    assert "career_ops_scan_completed" in telemetry_names


@pytest.mark.asyncio
async def test_run_career_ops_scan_failure_marks_failed_and_emits_event(db_session, monkeypatch):
    user_id = "career_ops_user_2"
    db_session.add(User(id=user_id, email="careerops2@example.com"))
    await db_session.commit()

    async def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("forced failure")

    monkeypatch.setattr(
        "services.career_ops_scan_service.recompute_job_scores_for_user",
        _boom,
    )

    payload = CareerOpsScanRunRequest(trigger_catalog_refresh=False)
    response = await run_career_ops_scan(session=db_session, user_id=user_id, payload=payload)

    assert response.status == "failed"
    assert response.error_code == "scan_failed"

    telemetry_names = (
        await db_session.execute(
            select(TelemetryEvent.event_name).where(TelemetryEvent.user_id == user_id)
        )
    ).scalars().all()
    assert "career_ops_scan_started" in telemetry_names
    assert "career_ops_scan_failed" in telemetry_names


@pytest.mark.asyncio
async def test_scan_history_persists_source_field(db_session):
    user_id = "career_ops_user_3"
    db_session.add(User(id=user_id, email="careerops3@example.com"))
    db_session.add(
        Job(
            id="job_cos_3",
            source="manual",
            external_id="cos-ext-3",
            title="ML Engineer",
            company="Gamma",
            location="Remote",
            description="Role three",
            url="https://example.com/jobs/3",
        )
    )
    db_session.add(
        JobScore(
            user_id=user_id,
            job_id="job_cos_3",
            fit_score=4.2,
            fit_reasons=["good fit"],
            risk_flags=[],
            dimension_scores={"tech": 4.2, "culture": 4.0, "seniority": 4.1, "comp": 4.0, "location": 4.5},
            scored_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    await run_career_ops_scan(
        session=db_session,
        user_id=user_id,
        payload=CareerOpsScanRunRequest(
            source="discover_page",
            trigger_catalog_refresh=False,
            min_fit_threshold=4.0,
        ),
    )

    history = await list_career_ops_scan_runs(session=db_session, user_id=user_id, limit=5)
    assert history.runs
    assert history.runs[0].source == "discover_page"


def test_scan_routes_delegate_to_service(client, monkeypatch):
    async def _fake_run_scan(*, session, user_id, payload):  # type: ignore[no-untyped-def]
        return CareerOpsScanRunResponse(
            scan_run_id="run_123",
            status="done",
            fetched=10,
            inserted=4,
            updated=3,
            deduped=3,
            scored=10,
            kept_after_threshold=5,
            queued_to_pipeline=2,
            top_job_ids=["job_1", "job_2"],
            duration_ms=456,
            error_code=None,
            error_detail=None,
        )

    async def _fake_list_scan_runs(*, session, user_id, limit):  # type: ignore[no-untyped-def]
        return CareerOpsScanHistoryResponse(runs=[])

    monkeypatch.setattr(jobs_router_module, "run_career_ops_scan", _fake_run_scan)
    monkeypatch.setattr(jobs_router_module, "list_career_ops_scan_runs", _fake_list_scan_runs)

    res = client.post(
        "/v1/jobs/scan/run",
        json={
            "query": "platform engineer",
            "min_fit_threshold": 4.0,
            "queue_top_n": 3,
            "trigger_catalog_refresh": False,
        },
    )
    assert res.status_code == 200
    assert res.json()["scan_run_id"] == "run_123"

    list_res = client.get("/v1/jobs/scan/runs?limit=10")
    assert list_res.status_code == 200
    assert list_res.json() == {"runs": []}
