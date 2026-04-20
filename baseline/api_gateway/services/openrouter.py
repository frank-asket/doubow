"""OpenRouter chat completions (OpenAI-compatible API)."""

from __future__ import annotations

import httpx

from config import settings


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


async def chat_completion(
    *,
    user_message: str,
    system_message: str,
) -> str:
    key = settings.openrouter_api_key
    if not key:
        raise RuntimeError("OpenRouter is not configured (missing OPENROUTER_API_KEY)")

    model_raw = (settings.openrouter_model or settings.anthropic_model or "").strip()
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
