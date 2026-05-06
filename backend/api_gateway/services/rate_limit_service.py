from __future__ import annotations

import asyncio
import math
import logging

from config import settings

logger = logging.getLogger(__name__)

_REDIS_LUA_SLIDING_WINDOW = """
local zset_key = KEYS[1]
local seq_key = KEYS[2]
local window_ms = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])

local now = redis.call('TIME')
local now_ms = now[1] * 1000 + math.floor(now[2] / 1000)
local min_score = now_ms - window_ms

redis.call('ZREMRANGEBYSCORE', zset_key, '-inf', min_score)
local count = redis.call('ZCARD', zset_key)
if count >= limit then
  local oldest = redis.call('ZRANGE', zset_key, 0, 0, 'WITHSCORES')
  local oldest_score = tonumber(oldest[2]) or now_ms
  return {0, oldest_score, now_ms}
end

local seq = redis.call('INCR', seq_key)
local member = tostring(now_ms) .. '-' .. tostring(seq)
redis.call('ZADD', zset_key, now_ms, member)

local ttl_ms = window_ms + 1000
redis.call('PEXPIRE', zset_key, ttl_ms)
redis.call('PEXPIRE', seq_key, ttl_ms)
return {1, -1, now_ms}
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


def _bucket_seq_key(*, bucket: str, user_id: str) -> str:
    return f"{_bucket_key(bucket=bucket, user_id=user_id)}:seq"


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
    seq_key = _bucket_seq_key(bucket=bucket, user_id=user_id)
    try:
        client = await _get_redis_client()
        result = await client.eval(
            _REDIS_LUA_SLIDING_WINDOW,
            2,
            key,
            seq_key,
            int(window_s * 1000),
            int(limit),
        )
        allowed = bool(int(result[0]))
        if allowed:
            return
        oldest_ms = int(result[1])
        now_ms = int(result[2])
        retry_after_ms = max(0, oldest_ms + int(window_s * 1000) - now_ms)
        retry_after = max(1, math.ceil(retry_after_ms / 1000)) if retry_after_ms > 0 else 1
        raise RateLimitExceededError(bucket=bucket, retry_after_s=retry_after)
    except RateLimitExceededError:
        raise
    except Exception as exc:
        if settings.rate_limit_fail_closed:
            raise RateLimitBackendUnavailableError("Rate-limit backend unavailable") from exc
        logger.warning("Rate-limit backend unavailable; proceeding without limit for bucket=%s", bucket, exc_info=True)
        return
