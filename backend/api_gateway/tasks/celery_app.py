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
    }
}

import tasks.send_tasks  # noqa: E402, F401 — register tasks
import tasks.discovery_task  # noqa: E402, F401 — register tasks
