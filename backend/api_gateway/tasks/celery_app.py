"""Shared Celery application instance for worker processes."""

from celery import Celery
from celery.schedules import crontab

from config import settings

celery_app = Celery(
    "doubow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    # Run twice daily (09:00 and 17:00 UTC) and fan out per user.
    "discovery-fanout-twice-daily": {
        "task": "tasks.discovery.run_discovery_task",
        "schedule": crontab(minute=0, hour="9,17"),
    },
    "ingest-all-sources": {
        "task": "ingestion.scheduler.ingest_all_sources",
        "schedule": crontab(minute="0", hour="*/6"),
    },
    "ingest-fast-sources": {
        "task": "ingestion.scheduler.ingest_fast_sources",
        "schedule": crontab(minute="30", hour="1,3,5,7,9,11,13,15,17,19,21,23"),
    },
    "ingestion-health-check": {
        "task": "ingestion.scheduler.health_check_all_connectors",
        "schedule": crontab(minute=0, hour=8),
    },
    "ingestion-cleanup-stale-jobs": {
        "task": "ingestion.scheduler.cleanup_stale_jobs",
        "schedule": crontab(minute=0, hour=3),
    },
    "job-alerts-daily-digest": {
        "task": "tasks.job_alerts.run_daily",
        "schedule": crontab(minute=30, hour=9),
    },
}

import tasks.send_tasks  # noqa: E402, F401 — register tasks
import tasks.autopilot_tasks  # noqa: E402, F401 — register tasks
import tasks.discovery_task  # noqa: E402, F401 — register tasks
import tasks.job_alert_tasks  # noqa: E402, F401 — register tasks
import ingestion.scheduler.celery_tasks  # noqa: E402, F401 — register tasks
