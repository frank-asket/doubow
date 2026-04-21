"""Entrypoint for ``celery -A tasks.worker worker`` — re-exports the shared app."""

from tasks.celery_app import celery_app

__all__ = ["celery_app"]
