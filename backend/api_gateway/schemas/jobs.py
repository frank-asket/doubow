from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

JobSource = Literal["ashby", "greenhouse", "lever", "linkedin", "wellfound", "manual", "catalog"]
Channel = Literal["email", "linkedin", "company_site"]


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
