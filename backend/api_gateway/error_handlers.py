from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from schemas.errors import ApiErrorBody, ErrorResponse


def _status_to_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "too_many_requests",
        500: "internal_error",
        502: "bad_gateway",
        503: "service_unavailable",
    }.get(status_code, "http_error")


def _message_from_detail(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        parts: list[str] = []
        for err in detail:
            if isinstance(err, dict):
                loc = ".".join(str(x) for x in err.get("loc", ()) if x != "body")
                msg = err.get("msg", "")
                parts.append(f"{loc}: {msg}" if loc else str(msg))
            else:
                parts.append(str(err))
        return "; ".join(parts) if parts else "Request validation failed"
    if isinstance(detail, dict):
        return str(detail.get("msg", detail))
    return str(detail)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        body = ErrorResponse(
            error=ApiErrorBody(
                code=_status_to_code(exc.status_code),
                message=_message_from_detail(exc.detail),
                details=exc.detail if isinstance(exc.detail, list) else None,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        body = ErrorResponse(
            error=ApiErrorBody(
                code="validation_error",
                message=_message_from_detail(exc.errors()),
                details=exc.errors(),
            )
        )
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))
