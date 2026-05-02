"""Request/response models for the TradingAgents-style job-search pipeline runner."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class JobSearchPipelineStageId(str, Enum):
    """Named stages in the end-to-end job search loop (ingest → profile → match → apply → learn)."""

    data_collection = "data_collection"
    resume_profile = "resume_profile"
    job_matching = "job_matching"
    outbound_application = "outbound_application"
    feedback = "feedback"


class JobSearchPipelineRunRequest(BaseModel):
    """Which stages to run and optional side effects (catalog refresh is expensive)."""

    stages: list[JobSearchPipelineStageId] | None = Field(
        default=None,
        description="If omitted, all stages run in default order.",
    )
    trigger_catalog_refresh: bool = Field(
        default=False,
        description="If true, runs multi-provider catalog ingest (Adzuna/Greenhouse/SerpAPI/optional connectors).",
    )
    catalog_preset: Literal["hourly", "daily"] = "hourly"
    include_legacy_connectors: bool = Field(
        default=False,
        description="Passed to catalog ingest when trigger_catalog_refresh is true.",
    )
    resume_aligned_catalog: bool = Field(
        default=True,
        description="When refreshing catalog, derive keywords/location from this user's resume.",
    )
    persist_feedback_learning: bool = Field(
        default=False,
        description="If true, merges the feedback-stage snapshot into resume.preferences.feedback_learning.",
    )


class PipelineStageOutcome(BaseModel):
    stage: JobSearchPipelineStageId
    ok: bool
    summary: str
    detail: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class JobSearchPipelineRunResponse(BaseModel):
    trace_id: str
    user_id: str
    stages: list[PipelineStageOutcome]
