from __future__ import annotations

import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from config import settings

logger = logging.getLogger(__name__)

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
LLM_OUTPUT_QUALITY_COUNT = Counter(
    "doubow_llm_output_quality_total",
    "Post-processing quality signals for LLM outputs by use-case/outcome",
    ["use_case", "outcome"],
)
API_ERRORS_TOTAL = Counter(
    "doubow_api_errors_total",
    "Unhandled API exceptions by method/path/error_type",
    ["method", "path", "error_type"],
)

_LOCAL_ORIGIN_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|host\.docker\.internal)(:\d+)?$")
_VERCEL_ORIGIN_RE = re.compile(r"^https://[a-z0-9]([a-z0-9-]*[a-z0-9])?\.vercel\.app$")


def _is_allowed_origin(origin: str) -> bool:
    if origin in settings.cors_origins:
        return True
    return bool(_LOCAL_ORIGIN_RE.match(origin) or _VERCEL_ORIGIN_RE.match(origin))


def _ensure_cors_headers(request: Request, response: Response) -> None:
    origin = request.headers.get("origin")
    if not origin or not _is_allowed_origin(origin):
        return
    # Preserve browser visibility of backend failures for allowed frontend origins.
    response.headers.setdefault("Access-Control-Allow-Origin", origin)
    response.headers.setdefault("Access-Control-Allow-Credentials", "true")
    vary = response.headers.get("Vary")
    if not vary:
        response.headers["Vary"] = "Origin"
    elif "origin" not in vary.lower():
        response.headers["Vary"] = f"{vary}, Origin"


async def metrics_middleware(request: Request, call_next):
    start = perf_counter()
    path = request.url.path
    request_id = (request.headers.get("X-Request-ID") or "").strip() or str(uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        API_ERRORS_TOTAL.labels(request.method, path, "unhandled_exception").inc()
        logger.exception("Unhandled API error method=%s path=%s request_id=%s", request.method, path, request_id)
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "details": None,
                }
            },
        )
        _ensure_cors_headers(request, response)
    finally:
        elapsed = perf_counter() - start
        REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
    response.headers.setdefault("X-Request-ID", request_id)
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
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


def observe_llm_output_quality(*, use_case: str, outcome: str) -> None:
    """Record post-processing quality outcomes for generated model outputs."""
    LLM_OUTPUT_QUALITY_COUNT.labels((use_case or "default").strip() or "default", (outcome or "unknown").strip()).inc()
