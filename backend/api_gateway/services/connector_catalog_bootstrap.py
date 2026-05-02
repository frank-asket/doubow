"""Ensure legacy SQL connector inserts participate in Discover by setting ``score_template``."""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from services.job_discovery_service import default_catalog_job_score_template

# Must match ``ingestion.scheduler.ingestion_engine.ALL_CONNECTORS`` keys.
LEGACY_CONNECTOR_SOURCES = frozenset(
    {"ashby", "greenhouse", "lever", "linkedin", "remotive", "wellfound", "ycombinator"}
)


async def ensure_score_templates_for_legacy_connector_jobs(session: AsyncSession) -> int:
    """Backfill ``score_template`` for connector-ingested rows that bypass ``discover_upsert_jobs``."""
    tpl = default_catalog_job_score_template()
    stmt = (
        update(Job)
        .where(Job.source.in_(LEGACY_CONNECTOR_SOURCES))
        .where(Job.score_template.is_(None))
        .values(score_template=tpl)
    )
    res = await session.execute(stmt)
    return int(res.rowcount or 0)
