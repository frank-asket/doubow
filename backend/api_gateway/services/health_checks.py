"""Dependency probes for orchestrator readiness (DB required, Redis best-effort)."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from config import settings
from db.session import engine

logger = logging.getLogger(__name__)

READINESS_DB_TIMEOUT_S = 3.0
READINESS_REDIS_TIMEOUT_S = 2.0


async def check_postgres() -> tuple[bool, str | None]:
    """Return (ok, error_message). Uses a cheap ``SELECT 1`` with timeout."""

    async def _ping() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    try:
        await asyncio.wait_for(_ping(), timeout=READINESS_DB_TIMEOUT_S)
        return True, None
    except Exception as exc:  # pragma: no cover - connection errors vary by driver
        logger.debug("health: postgres check failed", exc_info=True)
        return False, str(exc)


async def check_redis() -> tuple[bool, str | None]:
    """Return (ok, error_message). Optional: cache/Celery; API can run without Redis."""
    try:
        from redis.asyncio import Redis  # type: ignore[import-not-found]
    except ImportError:
        return False, "redis package not installed"

    client = Redis.from_url(settings.redis_url, socket_connect_timeout=1.0, decode_responses=True)
    try:
        await asyncio.wait_for(client.ping(), timeout=READINESS_REDIS_TIMEOUT_S)
        return True, None
    except Exception as exc:
        logger.debug("health: redis check failed", exc_info=True)
        return False, str(exc)
    finally:
        try:
            aclose = getattr(client, "aclose", None)
            if callable(aclose):
                await aclose()
            else:
                await client.close()  # redis-py 4.x async client
        except Exception:
            pass


async def check_celery_enqueue_health() -> tuple[bool, str | None]:
    """Return (ok, detail) for durable background enqueue path."""
    use_send = settings.use_celery_for_send_effective()
    use_autopilot = settings.use_celery_for_autopilot_effective()
    if not use_send and not use_autopilot:
        return True, "not_required"

    try:
        from tasks.send_tasks import health_ping_task

        # Lightweight broker check: enqueue a tiny task and return.
        health_ping_task.delay()
        return True, None
    except Exception as exc:
        logger.debug("health: celery enqueue check failed", exc_info=True)
        return False, str(exc)


async def gather_readiness() -> tuple[dict[str, object], int]:
    """Build JSON body and HTTP status for ``GET /ready``.

    Postgres failure → 503 (not ready). Redis failure → 200 with ``redis: degraded``.
    """
    pg_ok, pg_err = await check_postgres()
    redis_ok, redis_err = await check_redis()
    celery_ok, celery_err = await check_celery_enqueue_health()

    redis_label = "ok" if redis_ok else "degraded"
    background = {
        "send_mode": "celery" if settings.use_celery_for_send_effective() else "inprocess",
        "autopilot_mode": "celery" if settings.use_celery_for_autopilot_effective() else "inprocess",
        "allow_inprocess_fallback_in_production": settings.allow_inprocess_background_in_production,
        "enqueue": "ok" if celery_ok else "error",
    }
    if celery_err and celery_err != "not_required":
        background["enqueue_detail"] = celery_err

    if not pg_ok:
        return (
            {
                "status": "not_ready",
                "postgres": "error",
                "postgres_detail": pg_err,
                "redis": redis_label,
                "background_durability": background,
                **({"redis_detail": redis_err} if not redis_ok and redis_err else {}),
            },
            503,
        )

    body: dict[str, object] = {
        "status": "ready",
        "postgres": "ok",
        "redis": redis_label,
        "background_durability": background,
    }
    if not redis_ok and redis_err:
        body["redis_detail"] = redis_err
    return body, 200
