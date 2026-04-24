"""Celery discovery fanout task (2x daily per user)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from db.session import SessionLocal
from models.user import User
from schemas.jobs import DiscoverJobItem, DiscoverJobsRequest
from services.job_discovery_service import discover_upsert_jobs
from services.job_ingestion_sanitizer import normalize_optional_http_url
from services.portal_scanner import scan
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _normalize_job_payload(raw_jobs: list[dict]) -> DiscoverJobsRequest:
    jobs: list[DiscoverJobItem] = []
    for raw in raw_jobs:
        safe_url = normalize_optional_http_url(raw.get("url"))
        safe_logo_url = normalize_optional_http_url(raw.get("logo_url"))
        jobs.append(
            DiscoverJobItem(
                source=str(raw.get("source", "manual")),
                external_id=str(raw.get("external_id") or safe_url or f"generated-{len(jobs)}"),
                title=str(raw.get("title", "Untitled role")),
                company=str(raw.get("company", "Unknown company")),
                location=raw.get("location"),
                salary_range=raw.get("salary_range"),
                logo_url=safe_logo_url,
                description_raw=str(raw.get("description_raw", raw.get("description", ""))),
                description=str(raw.get("description", "")),
                url=safe_url or "",
                posted_at=raw.get("posted_at"),
                score_template=raw.get("score_template"),
            )
        )
    return DiscoverJobsRequest(jobs=jobs)


async def _run_discovery_task_async() -> dict[str, int]:
    async with SessionLocal() as session:
        user_ids = (await session.execute(select(User.id))).scalars().all()
        if not user_ids:
            logger.info("discovery_task: no users found; skipping")
            return {"users": 0, "created": 0, "updated": 0}

        discovered = await scan()
        if not discovered:
            logger.info("discovery_task: scanner returned no jobs")
            return {"users": len(user_ids), "created": 0, "updated": 0}

        payload = _normalize_job_payload(discovered)
        created_total = 0
        updated_total = 0
        for user_id in user_ids:
            result = await discover_upsert_jobs(session=session, user_id=user_id, payload=payload)
            created_total += result.created
            updated_total += result.updated

        logger.info(
            "discovery_task: fanout complete users=%s created=%s updated=%s at=%s",
            len(user_ids),
            created_total,
            updated_total,
            datetime.utcnow().isoformat(),
        )
        return {"users": len(user_ids), "created": created_total, "updated": updated_total}


@celery_app.task(name="tasks.discovery.run_discovery_task")
def run_discovery_task() -> dict[str, int]:
    return asyncio.run(_run_discovery_task_async())
