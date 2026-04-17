from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

JobSource = Literal["ashby", "greenhouse", "lever", "linkedin", "wellfound", "manual"]
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
    description: str
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
