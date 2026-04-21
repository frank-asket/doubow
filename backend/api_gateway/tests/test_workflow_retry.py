import pytest

from workflow.retry import async_retry


@pytest.mark.asyncio
async def test_async_retry_succeeds_first_try() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    result = await async_retry(
        op,
        attempts=3,
        base_delay_s=0.01,
        max_delay_s=0.02,
        retry_on=lambda _: True,
    )
    assert result == "ok"
    assert calls == 1


@pytest.mark.asyncio
async def test_async_retry_retries_then_succeeds() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise TimeoutError("transient")
        return "ok"

    result = await async_retry(
        op,
        attempts=3,
        base_delay_s=0.01,
        max_delay_s=0.02,
        retry_on=lambda exc: isinstance(exc, TimeoutError),
    )
    assert result == "ok"
    assert calls == 2


@pytest.mark.asyncio
async def test_async_retry_respects_retry_on_false() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        raise ValueError("fatal")

    with pytest.raises(ValueError, match="fatal"):
        await async_retry(
            op,
            attempts=3,
            base_delay_s=0.01,
            max_delay_s=0.02,
            retry_on=lambda exc: isinstance(exc, TimeoutError),
        )
    assert calls == 1


@pytest.mark.asyncio
async def test_async_retry_invalid_attempts() -> None:
    async def op() -> str:
        return "x"

    with pytest.raises(ValueError):
        await async_retry(
            op,
            attempts=0,
            base_delay_s=0.01,
            max_delay_s=0.02,
            retry_on=lambda _: True,
        )


@pytest.mark.asyncio
async def test_async_retry_exhausts_attempts() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        raise ConnectionError("still bad")

    with pytest.raises(ConnectionError):
        await async_retry(
            op,
            attempts=2,
            base_delay_s=0.01,
            max_delay_s=0.02,
            retry_on=lambda exc: isinstance(exc, ConnectionError),
        )
    assert calls == 2
