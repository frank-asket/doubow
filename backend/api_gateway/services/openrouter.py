"""OpenRouter chat completions (OpenAI-compatible API)."""

from __future__ import annotations

import json
import logging
import time
import httpx

from config import settings
from services.metrics import observe_llm_call
from workflow.retry import async_retry

logger = logging.getLogger(__name__)

# OpenAI-compatible tuning: temperature, max_tokens, top_p, frequency_penalty (OpenRouter forwards these).
_USE_CASE_DEFAULTS: dict[str, dict[str, float | int]] = {
    # Conversational orchestration: concise, mostly deterministic.
    "chat": {"temperature": 0.28, "max_tokens": 720, "top_p": 0.92},
    # Drafts: slight creativity; narrow nucleus sampling + light repetition penalty.
    "drafts": {"temperature": 0.45, "max_tokens": 900, "top_p": 0.9, "frequency_penalty": 0.12},
    # Prep: structured JSON or prose; balanced.
    "prep": {"temperature": 0.38, "max_tokens": 1200, "top_p": 0.94},
    # Resume analysis: factual, low temperature; full top_p allows ranked tokens.
    "resume": {"temperature": 0.2, "max_tokens": 1000, "top_p": 1.0},
}
_USE_CASE_RUNTIME_POLICY: dict[str, dict[str, float | int]] = {
    # Lower latency and quick feedback for UX chat streaming/completions.
    "chat": {"timeout_s": 45.0, "attempts": 2},
    # Draft quality with moderate retries.
    "drafts": {"timeout_s": 90.0, "attempts": 3},
    # Prep generation can run longer payloads.
    "prep": {"timeout_s": 120.0, "attempts": 3},
    # Resume analysis can run long and benefits from retries.
    "resume": {"timeout_s": 120.0, "attempts": 3},
}
_CIRCUIT_OPEN_AFTER_FAILURES = 2
_CIRCUIT_COOLDOWN_S = 20.0
_circuit_state: dict[str, dict[str, float | int]] = {}


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


def _get_policy(use_case_key: str) -> dict[str, float | int]:
    base = {"timeout_s": 120.0, "attempts": max(1, settings.openrouter_max_retries)}
    policy = _USE_CASE_RUNTIME_POLICY.get(use_case_key, {})
    merged = {**base, **policy}
    merged["attempts"] = max(1, int(merged["attempts"]))
    merged["timeout_s"] = max(5.0, float(merged["timeout_s"]))
    return merged


def _circuit_is_open(use_case_key: str) -> bool:
    state = _circuit_state.get(use_case_key)
    if not state:
        return False
    opened_at = float(state.get("opened_at", 0.0))
    if opened_at <= 0:
        return False
    if (time.monotonic() - opened_at) >= _CIRCUIT_COOLDOWN_S:
        _circuit_state[use_case_key] = {"failures": 0, "opened_at": 0.0}
        return False
    return True


def _record_success(use_case_key: str) -> None:
    _circuit_state[use_case_key] = {"failures": 0, "opened_at": 0.0}


def _record_failure(use_case_key: str) -> None:
    prev = _circuit_state.get(use_case_key, {"failures": 0, "opened_at": 0.0})
    failures = int(prev.get("failures", 0)) + 1
    opened_at = float(prev.get("opened_at", 0.0))
    if failures >= _CIRCUIT_OPEN_AFTER_FAILURES:
        opened_at = time.monotonic()
    _circuit_state[use_case_key] = {"failures": failures, "opened_at": opened_at}


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
    use_case_key = (use_case or "").strip().lower()
    policy = _get_policy(use_case_key)
    metric_use_case = use_case_key or "default"

    if _circuit_is_open(metric_use_case):
        raise RuntimeError(
            f"OpenRouter circuit temporarily open for use_case={metric_use_case}; retry shortly."
        )

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
    payload.update(_USE_CASE_DEFAULTS.get(use_case_key, {}))

    logger.debug(
        "openrouter.chat use_case=%s model=%s payload_keys=%s",
        use_case_key or "default",
        model,
        sorted(payload.keys()),
    )

    async def _once() -> str:
        async with httpx.AsyncClient(timeout=float(policy["timeout_s"])) as client:
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

    start = time.perf_counter()
    try:
        result = await async_retry(
            _once,
            attempts=int(policy["attempts"]),
            base_delay_s=settings.openrouter_retry_base_delay_s,
            max_delay_s=settings.openrouter_retry_max_delay_s,
            retry_on=_retry_openrouter,
        )
        _record_success(metric_use_case)
        observe_llm_call(
            use_case=metric_use_case,
            model=model,
            mode="chat",
            status="success",
            elapsed_s=time.perf_counter() - start,
        )
        return result
    except Exception:
        _record_failure(metric_use_case)
        observe_llm_call(
            use_case=metric_use_case,
            model=model,
            mode="chat",
            status="error",
            elapsed_s=time.perf_counter() - start,
        )
        raise


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
    use_case_key = (use_case or "").strip().lower()
    policy = _get_policy(use_case_key)
    metric_use_case = use_case_key or "default"

    if _circuit_is_open(metric_use_case):
        raise RuntimeError(
            f"OpenRouter circuit temporarily open for use_case={metric_use_case}; retry shortly."
        )

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
    payload.update(_USE_CASE_DEFAULTS.get(use_case_key, {}))

    logger.debug(
        "openrouter.stream use_case=%s model=%s payload_keys=%s",
        use_case_key or "default",
        model,
        sorted(payload.keys()),
    )

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=float(policy["timeout_s"])) as client:
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
        _record_success(metric_use_case)
        observe_llm_call(
            use_case=metric_use_case,
            model=model,
            mode="stream",
            status="success",
            elapsed_s=time.perf_counter() - start,
        )
    except Exception:
        _record_failure(metric_use_case)
        observe_llm_call(
            use_case=metric_use_case,
            model=model,
            mode="stream",
            status="error",
            elapsed_s=time.perf_counter() - start,
        )
        raise


def _reset_openrouter_circuit_state_for_tests() -> None:
    """Testing helper to avoid cross-test circuit state leaks."""
    _circuit_state.clear()
