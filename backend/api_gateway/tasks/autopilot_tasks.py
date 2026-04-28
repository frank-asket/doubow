"""Celery tasks for durable autopilot execution."""

import asyncio

from tasks.celery_app import celery_app


@celery_app.task(name="doubow.autopilot_run")
def autopilot_run_task(run_id: str, user_id: str, application_ids: list[str] | None = None) -> None:
    from services.autopilot_runner import execute_autopilot_run_background

    asyncio.run(execute_autopilot_run_background(run_id, user_id, application_ids))


@celery_app.task(name="doubow.autopilot_resume_run")
def autopilot_resume_run_task(run_id: str, user_id: str) -> None:
    from services.autopilot_resume import release_resume_slot
    from services.autopilot_runner import execute_autopilot_run_background

    try:
        asyncio.run(execute_autopilot_run_background(run_id, user_id, None))
    finally:
        release_resume_slot(run_id)

