"""Celery tasks for durable background work (optional; API falls back to FastAPI BackgroundTasks)."""

import asyncio

from tasks.celery_app import celery_app


@celery_app.task(name="doubow.send_approval_stub")
def send_approval_stub_task(approval_id: str, user_id: str) -> None:
    from services.send_approval_service import run_send_stub_in_background

    asyncio.run(run_send_stub_in_background(approval_id, user_id))


@celery_app.task(name="doubow.health_ping")
def health_ping_task() -> str:
    return "ok"
