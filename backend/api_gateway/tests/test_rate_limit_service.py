import pytest

from services import rate_limit_service


class _FakeRedisSlidingWindow:
    def __init__(self) -> None:
        self.now_ms = 0
        self.seq: dict[str, int] = {}
        self.data: dict[str, list[int]] = {}

    def advance(self, delta_ms: int) -> None:
        self.now_ms += delta_ms

    async def eval(
        self,
        _script: str,
        _num_keys: int,
        key: str,
        seq_key: str,
        window_ms: int,
        limit: int,
    ) -> list[int]:
        min_score = self.now_ms - int(window_ms)
        points = self.data.get(key, [])
        points = [score for score in points if score > min_score]
        self.data[key] = points
        if len(points) >= int(limit):
            oldest = points[0] if points else self.now_ms
            return [0, oldest, self.now_ms]
        self.seq[seq_key] = self.seq.get(seq_key, 0) + 1
        points.append(self.now_ms)
        points.sort()
        self.data[key] = points
        return [1, -1, self.now_ms]


class _FakeRedisFail:
    async def eval(self, _script: str, _num_keys: int, *_args) -> int:
        raise RuntimeError("redis unavailable")


@pytest.mark.asyncio
async def test_enforce_user_window_limit_allows_then_blocks(monkeypatch):
    fake = _FakeRedisSlidingWindow()
    monkeypatch.setattr(rate_limit_service, "_redis_client", fake)
    monkeypatch.setattr(rate_limit_service.settings, "rate_limit_redis_prefix", "ratelimit")

    await rate_limit_service.enforce_user_window_limit(
        bucket="agents_chat",
        user_id="user_1",
        limit=2,
        window_s=60,
    )
    await rate_limit_service.enforce_user_window_limit(
        bucket="agents_chat",
        user_id="user_1",
        limit=2,
        window_s=60,
    )
    with pytest.raises(rate_limit_service.RateLimitExceededError) as exc_info:
        await rate_limit_service.enforce_user_window_limit(
            bucket="agents_chat",
            user_id="user_1",
            limit=2,
            window_s=60,
        )
    assert exc_info.value.retry_after_s == 60


@pytest.mark.asyncio
async def test_enforce_user_window_limit_sliding_boundary_allows_at_exact_window(monkeypatch):
    fake = _FakeRedisSlidingWindow()
    monkeypatch.setattr(rate_limit_service, "_redis_client", fake)
    monkeypatch.setattr(rate_limit_service.settings, "rate_limit_redis_prefix", "ratelimit")

    await rate_limit_service.enforce_user_window_limit(
        bucket="agents_chat",
        user_id="user_boundary",
        limit=1,
        window_s=60,
    )
    fake.advance(60000)
    # At exactly +window, prior event falls out of (now-window, now] and next request is allowed.
    await rate_limit_service.enforce_user_window_limit(
        bucket="agents_chat",
        user_id="user_boundary",
        limit=1,
        window_s=60,
    )


@pytest.mark.asyncio
async def test_enforce_user_window_limit_fails_open_by_default(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "_redis_client", _FakeRedisFail())
    monkeypatch.setattr(rate_limit_service.settings, "rate_limit_fail_closed", False)

    await rate_limit_service.enforce_user_window_limit(
        bucket="agents_pipeline_run",
        user_id="user_2",
        limit=1,
        window_s=60,
    )


@pytest.mark.asyncio
async def test_enforce_user_window_limit_fail_closed_raises(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "_redis_client", _FakeRedisFail())
    monkeypatch.setattr(rate_limit_service.settings, "rate_limit_fail_closed", True)

    with pytest.raises(rate_limit_service.RateLimitBackendUnavailableError):
        await rate_limit_service.enforce_user_window_limit(
            bucket="agents_pipeline_run",
            user_id="user_3",
            limit=1,
            window_s=60,
        )
