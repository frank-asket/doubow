from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from schemas.jobs import DimensionScores, JobScore, JobsListResponse, JobWithScore

router = APIRouter(prefix="/jobs", tags=["jobs"])

NOW = datetime.now(timezone.utc)
MOCK_JOBS: list[JobWithScore] = [
    JobWithScore(
        id="job_001",
        source="greenhouse",
        external_id="gh_001",
        title="Senior ML Engineer",
        company="Mistral AI",
        location="Remote · Paris",
        salary_range="EUR130k-EUR160k",
        description="Build production RAG and agentic systems.",
        url="https://example.com/jobs/job_001",
        posted_at=NOW - timedelta(days=3),
        discovered_at=NOW - timedelta(hours=14),
        score=JobScore(
            job_id="job_001",
            fit_score=4.8,
            fit_reasons=["RAG and LLM stack is an exact match", "Strong platform engineering signals"],
            risk_flags=["Requires French work authorization"],
            dimension_scores=DimensionScores(tech=4.9, culture=4.5, seniority=4.9, comp=4.7, location=5.0),
            channel_recommendation="email",
            scored_at=NOW - timedelta(hours=6),
        ),
    ),
    JobWithScore(
        id="job_002",
        source="ashby",
        external_id="as_002",
        title="AI Product Engineer",
        company="Linear",
        location="Remote · Europe",
        salary_range="EUR110k-EUR145k",
        description="Ship user-facing AI features with strong product quality.",
        url="https://example.com/jobs/job_002",
        posted_at=NOW - timedelta(days=1),
        discovered_at=NOW - timedelta(hours=9),
        score=JobScore(
            job_id="job_002",
            fit_score=4.1,
            fit_reasons=["Strong product + AI blend", "Good salary/remote fit"],
            risk_flags=[],
            dimension_scores=DimensionScores(tech=4.2, culture=4.0, seniority=4.1, comp=4.2, location=4.4),
            channel_recommendation="linkedin",
            scored_at=NOW - timedelta(hours=4),
        ),
    ),
]


@router.get("", response_model=JobsListResponse)
async def list_jobs(
    min_fit: float = Query(default=0.0, ge=0.0, le=5.0),
    location: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
) -> JobsListResponse:
    filtered = [job for job in MOCK_JOBS if job.score.fit_score >= min_fit]
    if location:
        needle = location.strip().lower()
        filtered = [job for job in filtered if needle in job.location.lower()]
    return JobsListResponse(items=filtered, total=len(filtered), page=page, per_page=20)
