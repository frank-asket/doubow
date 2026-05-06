from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.career_ops_scan_run import CareerOpsScanRun
from models.job_score import JobScore
from schemas.applications import CreateApplicationRequest
from schemas.jobs import (
    CareerOpsScanHistoryItem,
    CareerOpsScanHistoryResponse,
    CareerOpsScanRunRequest,
    CareerOpsScanRunResponse,
)
from schemas.telemetry import TelemetryEventIn
from services.applications_service import (
    ApplicationIdempotencyConflictError,
    ApplicationJobNotFoundError,
    create_application,
)
from services.catalog_ingest_orchestrator import run_catalog_preset_ingest
from services.jobs_service import recompute_job_scores_for_user
from services.telemetry_service import record_event


async def run_career_ops_scan(
    *,
    session: AsyncSession,
    user_id: str,
    payload: CareerOpsScanRunRequest,
) -> CareerOpsScanRunResponse:
    run = CareerOpsScanRun(
        user_id=user_id,
        status="running",
        source=payload.source,
        query=payload.query,
        location=payload.location,
        sources_json=payload.sources or [],
        max_results=payload.max_results,
        min_fit_threshold=payload.min_fit_threshold,
        queue_top_n=payload.queue_top_n,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    await record_event(
        session=session,
        user_id=user_id,
        payload=TelemetryEventIn(
            event_name="career_ops_scan_started",
            properties={
                "scan_run_id": run.id,
                "source": payload.source,
                "query": payload.query,
                "location": payload.location,
                "source_count": len(payload.sources or []),
                "max_results": payload.max_results,
                "min_fit_threshold": payload.min_fit_threshold,
                "queue_top_n": payload.queue_top_n,
            },
        ),
    )

    started = datetime.now(UTC)
    try:
        ingest = None
        if payload.trigger_catalog_refresh:
            from config import settings

            ingest = await run_catalog_preset_ingest(
                session,
                settings,
                preset=payload.catalog_preset,
                user_id=user_id,
                keywords=payload.query,
                location=payload.location,
                country=None,
                start_page=1,
                resume_aligned=payload.resume_aligned_catalog,
                include_legacy_connectors=payload.include_legacy_connectors,
                include_scrapling=payload.include_scrapling,
            )
            run.inserted = int(ingest.created)
            run.updated = int(ingest.updated)
            run.deduped = int(ingest.deduped)
            run.source_mix_json = {p.provider: p.model_dump() for p in ingest.providers}
            run.fetched = int(ingest.created) + int(ingest.updated) + int(ingest.deduped)

        recomputed = await recompute_job_scores_for_user(session, user_id)
        run.scored = int(recomputed or 0)
        top_rows = (
            await session.execute(
                select(JobScore.job_id, JobScore.fit_score)
                .where(JobScore.user_id == user_id, JobScore.fit_score >= payload.min_fit_threshold)
                .order_by(desc(JobScore.fit_score), desc(JobScore.scored_at))
                .limit(payload.max_results)
            )
        ).all()
        top_job_ids = [str(row[0]) for row in top_rows]
        run.kept_after_threshold = len(top_job_ids)
        run.top_job_ids_json = top_job_ids
        await record_event(
            session=session,
            user_id=user_id,
            payload=TelemetryEventIn(
                event_name="career_ops_threshold_applied",
                properties={
                    "scan_run_id": run.id,
                    "min_fit_threshold": payload.min_fit_threshold,
                    "kept_after_threshold": len(top_job_ids),
                    "scored": run.scored,
                },
            ),
        )

        queued_count = 0
        for job_id in top_job_ids[: payload.queue_top_n]:
            try:
                await create_application(
                    session,
                    user_id,
                    CreateApplicationRequest(job_id=job_id, channel=payload.channel),
                )
                queued_count += 1
            except (ApplicationIdempotencyConflictError, ApplicationJobNotFoundError):
                continue
        run.queued_to_pipeline = queued_count
        if payload.queue_top_n > 0:
            await record_event(
                session=session,
                user_id=user_id,
                payload=TelemetryEventIn(
                    event_name="career_ops_queue_top_n_clicked",
                    properties={
                        "scan_run_id": run.id,
                        "queue_top_n": payload.queue_top_n,
                        "queued_to_pipeline": queued_count,
                        "channel": payload.channel,
                    },
                ),
            )
        run.status = "done"
        run.error_code = None
        run.error_detail = None
    except Exception as exc:
        run.status = "failed"
        run.error_code = "scan_failed"
        run.error_detail = str(exc)[:500]
    finally:
        finished = datetime.now(UTC)
        run.completed_at = finished
        run.duration_ms = int((finished - started).total_seconds() * 1000)
        await session.commit()
        await session.refresh(run)

    terminal_event = "career_ops_scan_completed" if run.status == "done" else "career_ops_scan_failed"
    await record_event(
        session=session,
        user_id=user_id,
        payload=TelemetryEventIn(
            event_name=terminal_event,  # type: ignore[arg-type]
            properties={
                "scan_run_id": run.id,
                "status": run.status,
                "source": payload.source,
                "query": payload.query,
                "location": payload.location,
                "source_count": len(payload.sources or []),
                "fetched": int(run.fetched or 0),
                "scored": int(run.scored or 0),
                "kept_after_threshold": int(run.kept_after_threshold or 0),
                "queued_to_pipeline": int(run.queued_to_pipeline or 0),
                "duration_ms": run.duration_ms,
                "min_fit_threshold": payload.min_fit_threshold,
            },
        ),
    )

    return CareerOpsScanRunResponse(
        scan_run_id=run.id,
        status=run.status,  # type: ignore[arg-type]
        fetched=int(run.fetched or 0),
        inserted=int(run.inserted or 0),
        updated=int(run.updated or 0),
        deduped=int(run.deduped or 0),
        scored=int(run.scored or 0),
        kept_after_threshold=int(run.kept_after_threshold or 0),
        queued_to_pipeline=int(run.queued_to_pipeline or 0),
        top_job_ids=list(run.top_job_ids_json or []),
        duration_ms=run.duration_ms,
        error_code=run.error_code,
        error_detail=run.error_detail,
    )


async def list_career_ops_scan_runs(
    *,
    session: AsyncSession,
    user_id: str,
    limit: int = 20,
) -> CareerOpsScanHistoryResponse:
    rows = (
        await session.execute(
            select(CareerOpsScanRun)
            .where(CareerOpsScanRun.user_id == user_id)
            .order_by(desc(CareerOpsScanRun.created_at), desc(CareerOpsScanRun.started_at))
            .limit(max(1, min(100, limit)))
        )
    ).scalars().all()
    return CareerOpsScanHistoryResponse(
        runs=[
            CareerOpsScanHistoryItem(
                scan_run_id=row.id,
                status=row.status,  # type: ignore[arg-type]
                source=row.source,
                query=row.query,
                location=row.location,
                sources=list(row.sources_json or []),
                max_results=int(row.max_results or 0),
                min_fit_threshold=float(row.min_fit_threshold or 0.0),
                queue_top_n=int(row.queue_top_n or 0),
                fetched=int(row.fetched or 0),
                inserted=int(row.inserted or 0),
                updated=int(row.updated or 0),
                deduped=int(row.deduped or 0),
                scored=int(row.scored or 0),
                kept_after_threshold=int(row.kept_after_threshold or 0),
                queued_to_pipeline=int(row.queued_to_pipeline or 0),
                duration_ms=row.duration_ms,
                started_at=row.started_at,
                completed_at=row.completed_at,
                created_at=row.created_at,
                error_code=row.error_code,
            )
            for row in rows
        ]
    )
