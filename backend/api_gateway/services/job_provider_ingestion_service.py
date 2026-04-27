"""Provider-driven ingestion that reuses discover_upsert_jobs catalog upsert flow."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job_ingestion_run import JobIngestionRun
from models.job_source_record import JobSourceRecord
from schemas.jobs import DiscoverJobsRequest, DiscoverJobsResponse
from services.job_discovery_service import discover_upsert_jobs
from services.provider_adapter import ProviderAdapter, ProviderFetchParams


async def ingest_provider_jobs(
    session: AsyncSession,
    *,
    user_id: str,
    adapter: ProviderAdapter,
    params: ProviderFetchParams,
) -> tuple[DiscoverJobsResponse, JobIngestionRun]:
    run = JobIngestionRun(provider=adapter.provider_name, status="running")
    session.add(run)
    await session.flush()

    try:
        fetched = await adapter.fetch_jobs(params)

        for provider_job_id, payload in fetched.raw_records:
            existing = (
                await session.execute(
                    select(JobSourceRecord).where(
                        JobSourceRecord.provider == fetched.provider,
                        JobSourceRecord.provider_job_id == provider_job_id,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    JobSourceRecord(
                        provider=fetched.provider,
                        provider_job_id=provider_job_id,
                        raw_payload=payload,
                    )
                )
            else:
                existing.raw_payload = payload
                existing.fetched_at = datetime.now(timezone.utc)

        if fetched.jobs:
            discover_payload = DiscoverJobsRequest(jobs=fetched.jobs)
            discover_result = await discover_upsert_jobs(
                session=session,
                user_id=user_id,
                payload=discover_payload,
                sync_scores=False,
            )
        else:
            discover_result = DiscoverJobsResponse(created=0, updated=0, job_ids=[])

        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        run.records_seen = len(fetched.raw_records)
        run.records_upserted = discover_result.created + discover_result.updated
        run.metadata_json = fetched.metadata
        await session.commit()
        return discover_result, run
    except Exception as exc:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = str(exc)[:4000]
        await session.commit()
        raise


async def ingest_provider_jobs_paginated(
    session: AsyncSession,
    *,
    user_id: str,
    adapter: ProviderAdapter,
    base_params: ProviderFetchParams,
    pages: int,
) -> dict:
    total_pages = max(1, pages)
    created = 0
    updated = 0
    job_ids: list[str] = []
    run_ids: list[str] = []
    for offset in range(total_pages):
        params = ProviderFetchParams(
            keywords=base_params.keywords,
            location=base_params.location,
            country=base_params.country,
            page=max(1, base_params.page) + offset,
            per_page=base_params.per_page,
            posted_after=base_params.posted_after,
        )
        result, run = await ingest_provider_jobs(session, user_id=user_id, adapter=adapter, params=params)
        created += result.created
        updated += result.updated
        job_ids.extend(result.job_ids)
        run_ids.append(run.id)

    return {
        "provider": adapter.provider_name,
        "pages": total_pages,
        "created": created,
        "updated": updated,
        "job_ids": job_ids,
        "run_ids": run_ids,
    }
