from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from ingestion.scheduler.celery_tasks import ingest_all_sources, ingest_single_source
from ingestion.scheduler.ingestion_engine import ALL_CONNECTORS
from models.user import User

router = APIRouter(prefix="/admin/ingestion", tags=["ingestion"])


@router.get("/status")
async def ingestion_status(
    _user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_session),
):
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
    _user: User = Depends(get_authenticated_user),
):
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
    _user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_session),
):
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
async def connector_health(_user: User = Depends(get_authenticated_user)):
    async def _check_one(name: str, connector_cls):
        try:
            return await connector_cls().health_check()
        except Exception as exc:
            return {"status": "error", "source": name, "error": str(exc)}

    results = await asyncio.gather(*[_check_one(name, cls) for name, cls in ALL_CONNECTORS.items()])
    healthy = sum(1 for result in results if result.get("status") == "ok")
    return {"healthy": healthy, "total": len(results), "results": results}

