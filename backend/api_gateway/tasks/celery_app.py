"""Shared Celery application instance for worker processes."""

from celery import Celery

from config import settings

celery_app = Celery(
    "doubow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

import tasks.send_tasks  # noqa: E402, F401 — register tasks
