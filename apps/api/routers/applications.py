from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Query

from schemas.applications import (
    Application,
    ApplicationsListResponse,
    CreateApplicationRequest,
    IntegrityChange,
    IntegrityCheckRequest,
    IntegrityCheckResponse,
    IntegritySummary,
)
from schemas.jobs import DimensionScores, Job, JobScore

router = APIRouter(prefix="/me/applications", tags=["applications"])

NOW = datetime.now(timezone.utc)
_JOB = Job(
    id="job_001",
    source="greenhouse",
    external_id="gh_001",
    title="Senior ML Engineer",
    company="Mistral AI",
    location="Remote · Paris",
    salary_range="EUR130k-EUR160k",
    description="Build production RAG and agentic systems.",
    url="https://example.com/jobs/job_001",
    posted_at=NOW,
    discovered_at=NOW,
)
_SCORE = JobScore(
    job_id="job_001",
    fit_score=4.8,
    fit_reasons=["Strong RAG match"],
    risk_flags=[],
    dimension_scores=DimensionScores(tech=4.9, culture=4.5, seniority=4.9, comp=4.7, location=5.0),
    channel_recommendation="email",
    scored_at=NOW,
)
APPLICATIONS: list[Application] = [
    Application(
        id="app_001",
        user_id="dev-user",
        job=_JOB,
        score=_SCORE,
        status="pending",
        channel="email",
        last_updated=NOW,
        is_stale=False,
    )
]


@router.get("", response_model=ApplicationsListResponse)
async def list_applications(status: str | None = Query(default=None)) -> ApplicationsListResponse:
    items = APPLICATIONS
    if status:
        items = [item for item in items if item.status == status]
    return ApplicationsListResponse(items=items, total=len(items), page=1, per_page=20)


@router.post("", response_model=Application)
async def create_application(payload: CreateApplicationRequest) -> Application:
    app = Application(
        id=f"app_{uuid4().hex[:8]}",
        user_id="dev-user",
        job=_JOB.model_copy(update={"id": payload.job_id}),
        score=_SCORE,
        status="pending",
        channel=payload.channel,
        last_updated=datetime.now(timezone.utc),
        idempotency_key=f"app-{uuid4().hex[:12]}",
        is_stale=False,
    )
    APPLICATIONS.insert(0, app)
    return app


@router.post("/integrity-check", response_model=IntegrityCheckResponse)
async def integrity_check(payload: IntegrityCheckRequest) -> IntegrityCheckResponse:
    stale_items = [a for a in APPLICATIONS if a.is_stale]
    dedup_items = [a for a in APPLICATIONS if a.dedup_group]
    changes: list[IntegrityChange] = []

    if dedup_items:
        ids = [item.id for item in dedup_items]
        changes.append(
            IntegrityChange(
                type="deduplicate",
                application_ids=ids,
                keep_id=ids[0],
                reason="Duplicate applications share the same dedup group",
            )
        )

    for item in stale_items:
        changes.append(
            IntegrityChange(
                type="mark_stale",
                application_ids=[item.id],
                reason="No update in the past 30 days.",
            )
        )

    if payload.mode == "apply":
        for item in APPLICATIONS:
            item.is_stale = False
            item.dedup_group = None

    summary = IntegritySummary(duplicates=len(dedup_items), stale=len(stale_items), status_fixes=0)
    return IntegrityCheckResponse(mode=payload.mode, summary=summary, changes=changes)
