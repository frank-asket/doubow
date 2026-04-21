from typing import Any

from pydantic import BaseModel, Field


class ApiErrorBody(BaseModel):
    """Stable machine-readable API error envelope (HTTP layer)."""

    code: str = Field(..., description="Stable error code for clients and logs")
    message: str = Field(..., description="Human-readable message safe to display")
    details: Any | None = Field(default=None, description="Optional structured validation or context")


class ErrorResponse(BaseModel):
    error: ApiErrorBody
