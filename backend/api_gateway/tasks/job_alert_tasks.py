"""Celery tasks for user-facing job alert digests."""

from __future__ import annotations

import asyncio
import logging

from db.session import SessionLocal
from services.job_alert_service import run_job_alerts_for_all_users
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_job_alerts_async(*, frequency: str) -> dict[str, int]:
    async with SessionLocal() as session:
        return await run_job_alerts_for_all_users(session, frequency=frequency)


@celery_app.task(name="tasks.job_alerts.run_daily")
def run_daily_job_alerts_task() -> dict[str, int]:
    out = asyncio.run(_run_job_alerts_async(frequency="daily"))
    logger.info(
        "job_alerts daily run users=%s candidates=%s sent=%s",
        out.get("users", 0),
        out.get("candidates", 0),
        out.get("sent", 0),
    )
    return out
