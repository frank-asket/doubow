from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import text

from db.session import SessionLocal
from ingestion.scheduler.ingestion_engine import ALL_CONNECTORS, run_ingestion


@shared_task(name="ingestion.scheduler.ingest_all_sources", time_limit=3600)
def ingest_all_sources():
    return asyncio.run(_run_ingestion(None))


@shared_task(name="ingestion.scheduler.ingest_fast_sources", time_limit=900)
def ingest_fast_sources():
    return asyncio.run(_run_ingestion(["greenhouse", "ashby", "lever", "remotive", "ycombinator"]))


@shared_task(name="ingestion.scheduler.ingest_single_source", time_limit=900)
def ingest_single_source(source_name: str):
    return asyncio.run(_run_ingestion([source_name]))


@shared_task(name="ingestion.scheduler.health_check_all_connectors", time_limit=300)
def health_check_all_connectors():
    async def _run() -> dict:
        results: dict[str, dict] = {}
        for name, connector_cls in ALL_CONNECTORS.items():
            try:
                results[name] = await connector_cls().health_check()
            except Exception as exc:
                results[name] = {"status": "error", "source": name, "error": str(exc)}
        return results

    return asyncio.run(_run())


@shared_task(name="ingestion.scheduler.cleanup_stale_jobs", time_limit=300)
def cleanup_stale_jobs(days_old: int = 30):
    async def _cleanup() -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        async with SessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    UPDATE jobs
                    SET is_active = false
                    WHERE is_active = true AND discovered_at < :cutoff
                    RETURNING id
                    """
                ),
                {"cutoff": cutoff.isoformat()},
            )
            count = len(result.fetchall())
            await session.commit()
            return {"deactivated": count}

    return asyncio.run(_cleanup())


async def _run_ingestion(connector_names: list[str] | None):
    async with SessionLocal() as session:
        summary = await run_ingestion(session, connector_names=connector_names)
        return summary.to_dict()

