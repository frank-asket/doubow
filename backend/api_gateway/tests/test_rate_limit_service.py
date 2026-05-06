import pytest

from services import rate_limit_service


class _FakeRedisCounter:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def eval(self, _script: str, _num_keys: int, key: str, window_s: int) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        if self.counts[key] == 1:
            self.ttls[key] = int(window_s)
        return self.counts[key]

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, 0)


class _FakeRedisFail:
    async def eval(self, _script: str, _num_keys: int, _key: str, _window_s: int) -> int:
        raise RuntimeError("redis unavailable")

    async def ttl(self, _key: str) -> int:
        return 0


@pytest.mark.asyncio
async def test_enforce_user_window_limit_allows_then_blocks(monkeypatch):
    fake = _FakeRedisCounter()
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
