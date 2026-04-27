"""Provider-driven ingestion that reuses discover_upsert_jobs catalog upsert flow."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from models.job_ingestion_run import JobIngestionRun
from models.job_source_record import JobSourceRecord
from schemas.jobs import DiscoverJobItem, DiscoverJobsRequest, DiscoverJobsResponse
from services.job_discovery_service import discover_upsert_jobs
from services.provider_adapter import ProviderAdapter, ProviderFetchParams


_FP_SPLIT = re.compile(r"\s+")


def _text(v: str | None) -> str:
    return _FP_SPLIT.sub(" ", (v or "").strip().lower())


def _fingerprint(item: DiscoverJobItem) -> str:
    return f"{_text(item.title)}|{_text(item.company)}|{_text(item.location or '')}"


async def _dedupe_jobs(session: AsyncSession, items: list[DiscoverJobItem]) -> tuple[list[DiscoverJobItem], int]:
    if not items:
        return [], 0

    # In-feed dedupe first.
    unique: list[DiscoverJobItem] = []
    seen_fp: set[str] = set()
    for it in items:
        fp = _fingerprint(it)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        unique.append(it)

    companies = list({_text(it.company) for it in unique if _text(it.company)})
    existing_rows = (
        await session.execute(
            select(Job.title, Job.company, Job.location).where(func.lower(Job.company).in_(companies))
        )
    ).all() if companies else []
    existing_fp = {
        f"{_text(title)}|{_text(company)}|{_text(location or '')}"
        for title, company, location in existing_rows
    }

    filtered = [it for it in unique if _fingerprint(it) not in existing_fp]
    deduped = len(items) - len(filtered)
    return filtered, deduped


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
        deduped_jobs, deduped_count = await _dedupe_jobs(session, fetched.jobs)

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

        if deduped_jobs:
            discover_payload = DiscoverJobsRequest(jobs=deduped_jobs)
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
        run.metadata_json = {**(fetched.metadata or {}), "deduped_count": deduped_count}
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
    deduped_total = 0
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
        deduped_total += int((run.metadata_json or {}).get("deduped_count") or 0)

    return {
        "provider": adapter.provider_name,
        "pages": total_pages,
        "created": created,
        "updated": updated,
        "job_ids": job_ids,
        "run_ids": run_ids,
        "deduped": deduped_total,
    }
