"""OpenRouter chat completions (OpenAI-compatible API)."""

from __future__ import annotations

import json
import logging
import httpx

from config import settings
from workflow.retry import async_retry

logger = logging.getLogger(__name__)


def normalize_openrouter_model_id(model: str) -> str:
    """OpenRouter expects `provider/model`. Accept bare Anthropic-style ids for backwards compatibility."""
    m = model.strip()
    if not m:
        return m
    if "/" in m:
        return m
    if m.startswith("claude-"):
        return f"anthropic/{m}"
    return m


def _retry_openrouter(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {408, 425, 429, 500, 502, 503, 504}
    return False


async def chat_completion(
    *,
    user_message: str,
    system_message: str,
    use_case: str | None = None,
    model_override: str | None = None,
) -> str:
    key = settings.openrouter_api_key
    if not key:
        raise RuntimeError("OpenRouter is not configured (missing OPENROUTER_API_KEY)")

    model_raw = (model_override or settings.resolve_openrouter_model(use_case)).strip()
    if not model_raw:
        raise RuntimeError("OpenRouter model not set (OPENROUTER_MODEL or ANTHROPIC_MODEL)")
    model = normalize_openrouter_model_id(model_raw)

    base = settings.openrouter_api_url.rstrip("/")
    url = f"{base}/chat/completions"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    }

    async def _once() -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("OpenRouter returned no choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenRouter returned empty content")

        return content.strip()

    return await async_retry(
        _once,
        attempts=max(1, settings.openrouter_max_retries),
        base_delay_s=settings.openrouter_retry_base_delay_s,
        max_delay_s=settings.openrouter_retry_max_delay_s,
        retry_on=_retry_openrouter,
    )


async def stream_chat_completion_chunks(
    *,
    user_message: str,
    system_message: str,
    use_case: str | None = None,
    model_override: str | None = None,
):
    """Yield text fragments from OpenRouter streaming chat completions (OpenAI-compatible SSE)."""
    key = settings.openrouter_api_key
    if not key:
        raise RuntimeError("OpenRouter is not configured (missing OPENROUTER_API_KEY)")

    model_raw = (model_override or settings.resolve_openrouter_model(use_case)).strip()
    if not model_raw:
        raise RuntimeError("OpenRouter model not set (OPENROUTER_MODEL or ANTHROPIC_MODEL)")
    model = normalize_openrouter_model_id(model_raw)

    base = settings.openrouter_api_url.rstrip("/")
    url = f"{base}/chat/completions"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if line == "data: [DONE]":
                    break
                if not line.startswith("data: "):
                    continue
                raw = line[6:].strip()
                if raw == "[DONE]":
                    break
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    logger.debug("openrouter stream skip line=%s", raw[:80])
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if isinstance(content, str) and content:
                    yield content
