from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_session
from dependencies import get_authenticated_user
from ingestion.scheduler.celery_tasks import ingest_all_sources, ingest_single_source
from ingestion.scheduler.ingestion_engine import ALL_CONNECTORS
from models.user import User
from services.rate_limit_service import (
    RateLimitBackendUnavailableError,
    RateLimitExceededError,
    enforce_user_window_limit,
)

router = APIRouter(prefix="/admin/ingestion", tags=["ingestion"])


def _require_ingestion_admin(user: User) -> None:
    allowed_ids = set(settings.admin_ingestion_user_ids_list())
    # Keep local/dev fast unless explicit allow-list is configured.
    if settings.environment.lower() != "production" and not allowed_ids:
        return
    if user.id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin ingestion access is restricted",
        )


async def _enforce_ingestion_limit(*, bucket: str, user_id: str, limit: int, window_s: int) -> None:
    try:
        await enforce_user_window_limit(bucket=bucket, user_id=user_id, limit=limit, window_s=window_s)
    except RateLimitExceededError as exc:
        headers = {"Retry-After": str(exc.retry_after_s)} if exc.retry_after_s is not None else None
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {bucket}. Please retry shortly.",
            headers=headers,
        ) from exc
    except RateLimitBackendUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter temporarily unavailable",
        ) from exc


@router.get("/status")
async def ingestion_status(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_session),
):
    _require_ingestion_admin(user)
    total = (
        await db.execute(
            text("SELECT COUNT(*) FROM jobs WHERE coalesce(is_active, true) = true")
        )
    ).scalar()
    by_source_rows = (
        await db.execute(
            text(
                """
                SELECT source, COUNT(*) AS cnt, MAX(discovered_at) AS last_seen
                FROM jobs
                WHERE coalesce(is_active, true) = true
                GROUP BY source
                ORDER BY cnt DESC
                """
            )
        )
    ).fetchall()
    by_source = [
        {"source": row[0], "count": row[1], "last_discovered": row[2].isoformat() if row[2] else None}
        for row in by_source_rows
    ]
    last_run_row = (
        await db.execute(
            text(
                """
                SELECT run_id, started_at, completed_at, total_fetched, total_inserted, total_errors
                FROM ingestion_runs
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
        )
    ).fetchone()
    last_run = (
        {
            "run_id": last_run_row[0],
            "started_at": last_run_row[1].isoformat() if last_run_row[1] else None,
            "completed_at": last_run_row[2].isoformat() if last_run_row[2] else None,
            "fetched": last_run_row[3],
            "inserted": last_run_row[4],
            "errors": last_run_row[5],
        }
        if last_run_row
        else None
    )
    return {
        "total_active_jobs": total or 0,
        "by_source": by_source,
        "sources_active": len(by_source),
        "sources_total": len(ALL_CONNECTORS),
        "last_run": last_run,
    }


@router.post("/run")
async def trigger_ingestion(
    source: str | None = None,
    user: User = Depends(get_authenticated_user),
):
    _require_ingestion_admin(user)
    await _enforce_ingestion_limit(
        bucket="ingestion_run",
        user_id=user.id,
        limit=settings.ingestion_run_max_requests_per_window,
        window_s=settings.ingestion_run_window_seconds,
    )
    if source:
        if source not in ALL_CONNECTORS:
            raise HTTPException(status_code=422, detail=f"Unknown source '{source}'")
        task = ingest_single_source.delay(source)
        return {"status": "queued", "task_id": task.id, "source": source}
    task = ingest_all_sources.delay()
    return {"status": "queued", "task_id": task.id, "source": "all"}


@router.get("/runs")
async def ingestion_runs(
    limit: int = Query(default=20, ge=1, le=200),
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_session),
):
    _require_ingestion_admin(user)
    rows = (
        await db.execute(
            text(
                """
                SELECT run_id, started_at, completed_at, total_fetched, total_inserted, total_dupes, total_errors, results_json
                FROM ingestion_runs
                ORDER BY started_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
    ).fetchall()
    return [
        {
            "run_id": row[0],
            "started_at": row[1].isoformat() if row[1] else None,
            "completed_at": row[2].isoformat() if row[2] else None,
            "fetched": row[3],
            "inserted": row[4],
            "dupes": row[5],
            "errors": row[6],
            "by_source": json.loads(row[7]) if row[7] else [],
        }
        for row in rows
    ]


@router.get("/health")
async def connector_health(user: User = Depends(get_authenticated_user)):
    _require_ingestion_admin(user)
    await _enforce_ingestion_limit(
        bucket="ingestion_health",
        user_id=user.id,
        limit=settings.ingestion_health_max_requests_per_window,
        window_s=settings.ingestion_health_window_seconds,
    )

    async def _check_one(name: str, connector_cls):
        try:
            return await connector_cls().health_check()
        except Exception as exc:
            return {"status": "error", "source": name, "error": str(exc)}

    results = await asyncio.gather(*[_check_one(name, cls) for name, cls in ALL_CONNECTORS.items()])
    healthy = sum(1 for result in results if result.get("status") == "ok")
    return {"healthy": healthy, "total": len(results), "results": results}

