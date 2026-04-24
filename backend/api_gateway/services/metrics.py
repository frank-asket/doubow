from __future__ import annotations

from time import perf_counter

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "doubow_api_requests_total",
    "Total API requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "doubow_api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "path"],
)
LLM_CALL_COUNT = Counter(
    "doubow_llm_calls_total",
    "Total LLM calls by use-case/model/mode/status",
    ["use_case", "model", "mode", "status"],
)
LLM_CALL_LATENCY = Histogram(
    "doubow_llm_call_duration_seconds",
    "LLM call latency in seconds by use-case/model/mode",
    ["use_case", "model", "mode"],
)


async def metrics_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    elapsed = perf_counter() - start
    path = request.url.path
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
    return response


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def observe_llm_call(
    *,
    use_case: str,
    model: str,
    mode: str,
    status: str,
    elapsed_s: float,
) -> None:
    """Record backend LLM call metrics."""
    LLM_CALL_COUNT.labels(use_case, model, mode, status).inc()
    LLM_CALL_LATENCY.labels(use_case, model, mode).observe(max(0.0, elapsed_s))
