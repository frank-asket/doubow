from __future__ import annotations

import asyncio
import logging

from config import settings

logger = logging.getLogger(__name__)

_REDIS_LUA_INCR_WITH_EXPIRE = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""

_redis_client = None
_redis_client_lock = asyncio.Lock()


class RateLimitExceededError(Exception):
    def __init__(self, *, bucket: str, retry_after_s: int | None = None) -> None:
        self.bucket = bucket
        self.retry_after_s = retry_after_s
        super().__init__(f"Rate limit exceeded for {bucket}")


class RateLimitBackendUnavailableError(RuntimeError):
    pass


def _bucket_key(*, bucket: str, user_id: str) -> str:
    prefix = (settings.rate_limit_redis_prefix or "ratelimit").strip() or "ratelimit"
    return f"{prefix}:{bucket}:{user_id}"


async def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    async with _redis_client_lock:
        if _redis_client is not None:
            return _redis_client
        from redis.asyncio import Redis  # type: ignore[import-not-found]

        _redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=1.0, decode_responses=False)
        return _redis_client


async def close_rate_limit_client() -> None:
    global _redis_client
    client = _redis_client
    _redis_client = None
    if client is None:
        return
    try:
        aclose = getattr(client, "aclose", None)
        if callable(aclose):
            await aclose()
        else:
            await client.close()
    except Exception:
        logger.debug("Failed to close Redis rate-limit client", exc_info=True)


async def enforce_user_window_limit(*, bucket: str, user_id: str, limit: int, window_s: int) -> None:
    if limit <= 0 or window_s <= 0:
        return
    key = _bucket_key(bucket=bucket, user_id=user_id)
    try:
        client = await _get_redis_client()
        count = int(await client.eval(_REDIS_LUA_INCR_WITH_EXPIRE, 1, key, window_s))
        if count <= limit:
            return
        ttl = await client.ttl(key)
        retry_after = int(ttl) if isinstance(ttl, int) and ttl > 0 else None
        raise RateLimitExceededError(bucket=bucket, retry_after_s=retry_after)
    except RateLimitExceededError:
        raise
    except Exception as exc:
        if settings.rate_limit_fail_closed:
            raise RateLimitBackendUnavailableError("Rate-limit backend unavailable") from exc
        logger.warning("Rate-limit backend unavailable; proceeding without limit for bucket=%s", bucket, exc_info=True)
        return
