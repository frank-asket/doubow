from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

JobSource = Literal[
    "adzuna",
    "ashby",
    "catalog",
    "greenhouse",
    "lever",
    "linkedin",
    "manual",
    "scrapling",
    "wellfound",
]
Channel = Literal["email", "linkedin", "company_site"]
ScoreProvenance = Literal["computed", "template_default", "template_seeded", "unknown"]


class DimensionScores(BaseModel):
    tech: float = Field(ge=0.0, le=5.0)
    culture: float = Field(ge=0.0, le=5.0)
    seniority: float = Field(ge=0.0, le=5.0)
    comp: float = Field(ge=0.0, le=5.0)
    location: float = Field(ge=0.0, le=5.0)


class JobScore(BaseModel):
    job_id: str
    fit_score: float = Field(ge=1.0, le=5.0)
    fit_reasons: list[str]
    risk_flags: list[str]
    dimension_scores: DimensionScores
    channel_recommendation: Channel
    scored_at: datetime
    provenance: ScoreProvenance = "unknown"


class Job(BaseModel):
    id: str
    source: JobSource
    external_id: str
    title: str
    company: str
    location: str
    salary_range: str | None = None
    logo_url: str | None = None
    description_raw: str = ""
    description_clean: str = ""
    description: str
    canonical_url: str = ""
    url: str
    posted_at: datetime | None = None
    discovered_at: datetime


class JobWithScore(Job):
    score: JobScore


class JobsListResponse(BaseModel):
    items: list[JobWithScore]
    total: int
    page: int
    per_page: int


class DiscoverJobItem(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    salary_range: str | None = Field(default=None, max_length=128)
    logo_url: str | None = Field(default=None, max_length=1000)
    description_raw: str = ""
    description: str = ""
    url: str = ""
    posted_at: datetime | None = None
    score_template: dict | None = None


class DiscoverJobsRequest(BaseModel):
    jobs: list[DiscoverJobItem] = Field(min_length=1, max_length=100)


class DiscoverJobsResponse(BaseModel):
    created: int
    updated: int
    job_ids: list[str]


class AdzunaIngestRequest(BaseModel):
    keywords: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=8)
    start_page: int = Field(default=1, ge=1)
    pages: int = Field(default=1, ge=1, le=20)
    per_page: int = Field(default=50, ge=1, le=50)


class AdzunaIngestResponse(BaseModel):
    provider: str
    pages: int
    created: int
    updated: int
    run_ids: list[str]
    job_ids: list[str]


class GreenhouseIngestRequest(BaseModel):
    board_tokens: list[str] | None = None
    keywords: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    start_page: int = Field(default=1, ge=1)
    pages: int = Field(default=1, ge=1, le=20)
    per_page: int = Field(default=50, ge=1, le=50)


class GreenhouseIngestResponse(BaseModel):
    provider: str
    pages: int
    created: int
    updated: int
    run_ids: list[str]
    job_ids: list[str]
    deduped: int = 0


class ScraplingIngestRequest(BaseModel):
    """Query context for Scrapling (runtime hook may use keywords/location; fixture ignores them)."""

    keywords: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)


class ScraplingIngestResponse(BaseModel):
    provider: str = "scrapling"
    pages: int = 1
    created: int
    updated: int
    run_ids: list[str]
    job_ids: list[str]
    deduped: int = 0


class AdzunaPresetIngestResponse(AdzunaIngestResponse):
    preset: Literal["hourly", "daily"]
    catalog_actor_user_id: str = Field(description="User id used for ingestion runs (typically JOB_CATALOG_INGESTION_USER_ID)")


class GreenhousePresetIngestResponse(GreenhouseIngestResponse):
    preset: Literal["hourly", "daily"]
    catalog_actor_user_id: str = Field(description="User id used for ingestion runs (typically JOB_CATALOG_INGESTION_USER_ID)")


class ProviderIngestSummary(BaseModel):
    provider: str
    status: Literal["completed", "failed", "skipped"]
    pages: int = 0
    created: int = 0
    updated: int = 0
    deduped: int = 0
    run_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class CatalogPresetIngestResponse(BaseModel):
    preset: Literal["hourly", "daily"]
    catalog_actor_user_id: str
    status: Literal["ok", "partial", "failed"]
    providers: list[ProviderIngestSummary]
    created: int
    updated: int
    deduped: int = 0
    run_ids: list[str]
    job_ids: list[str]


class JobScoresRecomputeResponse(BaseModel):
    user_id: str
    refreshed_scores: int


class CareerOpsScanRunRequest(BaseModel):
    source: str | None = Field(default=None, max_length=64)
    query: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    sources: list[str] | None = Field(default=None, max_length=20)
    max_results: int = Field(default=100, ge=1, le=500)
    min_fit_threshold: float = Field(default=0.0, ge=0.0, le=5.0)
    queue_top_n: int = Field(default=0, ge=0, le=20)
    channel: Channel = "email"
    trigger_catalog_refresh: bool = True
    catalog_preset: Literal["hourly", "daily"] = "hourly"
    include_legacy_connectors: bool = False
    include_scrapling: bool = True
    resume_aligned_catalog: bool = True


class CareerOpsScanRunResponse(BaseModel):
    scan_run_id: str
    status: Literal["queued", "running", "done", "failed"]
    fetched: int
    inserted: int
    updated: int
    deduped: int
    scored: int
    kept_after_threshold: int
    queued_to_pipeline: int
    top_job_ids: list[str] = Field(default_factory=list)
    duration_ms: int | None = None
    error_code: str | None = None
    error_detail: str | None = None


class CareerOpsScanHistoryItem(BaseModel):
    scan_run_id: str
    status: Literal["queued", "running", "done", "failed"]
    source: str | None = None
    query: str | None = None
    location: str | None = None
    sources: list[str] = Field(default_factory=list)
    max_results: int
    min_fit_threshold: float
    queue_top_n: int
    fetched: int
    inserted: int
    updated: int
    deduped: int
    scored: int
    kept_after_threshold: int
    queued_to_pipeline: int
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    error_code: str | None = None


class CareerOpsScanHistoryResponse(BaseModel):
    runs: list[CareerOpsScanHistoryItem]
