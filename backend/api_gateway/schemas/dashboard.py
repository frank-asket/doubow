from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    """Aggregates for sidebar badges and Discover stat strip (global, not paginated list)."""

    high_fit_count: int = Field(
        ...,
        description="Jobs scored above threshold (default 4.0) — Discover badge / ‘ready to review’",
    )
    pipeline_count: int = Field(..., description="Total applications for this user")
    pending_approvals: int = Field(..., description="Approvals awaiting review")
    evaluated_this_week: int = Field(
        ...,
        description="Job scores recorded since Monday 00:00 UTC of the current ISO week",
    )
    avg_fit_score: float | None = Field(
        None,
        description="Mean fit_score across all scored jobs for this user (None if none)",
    )
    applied_awaiting_reply: int = Field(
        ...,
        description="Applications in pending, applied, or interview status",
    )
    total_scored_jobs: int = Field(..., description="Total job_scores rows for this user")
    profile_views: int | None = Field(
        default=None,
        description=(
            "Employer/recruiter profile impressions for this user when tracked; "
            "omit/null until analytics populates — clients may show discover coverage instead."
        ),
    )
    response_rate_pct: int | None = Field(
        None,
        description=(
            "Share of submitted applications (applied+) that reached an employer-visible outcome "
            "(interview, offer, or rejection). Null when there are no submitted applications."
        ),
    )
