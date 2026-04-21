"""Limited retries for outbound HTTP / LLM calls (transient failures only)."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def async_retry(
    op: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    base_delay_s: float,
    max_delay_s: float,
    retry_on: Callable[[BaseException], bool],
) -> T:
    """Run ``op`` with exponential backoff + jitter after failures where ``retry_on(exc)`` is True."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            return await op()
        except BaseException as exc:
            last_exc = exc
            if attempt >= attempts - 1 or not retry_on(exc):
                raise
            delay = min(max_delay_s, base_delay_s * (2**attempt))
            jitter = random.uniform(0, delay * 0.25)
            await asyncio.sleep(delay + jitter)

    assert last_exc is not None
    raise last_exc
