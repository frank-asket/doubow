from __future__ import annotations

import logging
from functools import lru_cache

from config import settings
from schemas.jobs import JobsListResponse

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_redis_client():
    try:
        from redis.asyncio import Redis  # type: ignore[import-not-found]
    except Exception:
        return None
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


def jobs_list_cache_key(*, user_id: str, min_fit: float, location: str | None, page: int, per_page: int) -> str:
    loc = (location or "").strip().lower()
    return f"jobs:list:v1:{user_id}:{min_fit:.2f}:{loc}:{page}:{per_page}"


async def get_cached_jobs_list(key: str) -> JobsListResponse | None:
    client = _get_redis_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
    except Exception:
        logger.debug("jobs_cache: redis get failed key=%s", key, exc_info=True)
        return None
    if not raw:
        return None
    try:
        return JobsListResponse.model_validate_json(raw)
    except Exception:
        return None


async def set_cached_jobs_list(key: str, payload: JobsListResponse) -> None:
    client = _get_redis_client()
    if client is None:
        return
    try:
        await client.set(key, payload.model_dump_json(), ex=settings.jobs_cache_ttl_seconds)
    except Exception:
        logger.debug("jobs_cache: redis set failed key=%s", key, exc_info=True)


async def invalidate_user_jobs_list_cache(user_id: str) -> None:
    client = _get_redis_client()
    if client is None:
        return
    pattern = f"jobs:list:v1:{user_id}:*"
    try:
        keys = [key async for key in client.scan_iter(match=pattern)]
        if keys:
            await client.delete(*keys)
    except Exception:
        logger.debug("jobs_cache: invalidate failed user_id=%s", user_id, exc_info=True)
