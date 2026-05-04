from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.errors import ErrorResponse
from schemas.jobs import (
    AdzunaIngestRequest,
    AdzunaIngestResponse,
    AdzunaPresetIngestResponse,
    CatalogPresetIngestResponse,
    DiscoverJobsRequest,
    DiscoverJobsResponse,
    GreenhouseIngestRequest,
    GreenhouseIngestResponse,
    GreenhousePresetIngestResponse,
    JobsListResponse,
    JobScoresRecomputeResponse,
    ScraplingIngestRequest,
    ScraplingIngestResponse,
)
from services.adzuna_adapter import AdzunaAdapter, resolve_adzuna_scheduled_ingest_params
from services.greenhouse_adapter import GreenhouseAdapter, resolve_greenhouse_scheduled_ingest_params
from services.job_discovery_service import discover_upsert_jobs
from services.catalog_ingest_orchestrator import run_catalog_preset_ingest
from services.job_provider_ingestion_service import ingest_provider_jobs, ingest_provider_jobs_paginated
from services.scrapling_adapter import ScraplingAdapter
from services.provider_adapter import ProviderFetchParams
from services.jobs_service import (
    dismiss_job_for_user,
    list_jobs as list_jobs_service,
    recompute_job_scores_for_user,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


class IngestSchedulePreset(str, Enum):
    """Shared hourly/daily buckets for Adzuna, Greenhouse, and multi-provider catalog ingestion."""

    hourly = "hourly"
    daily = "daily"


# Backwards-compatible alias (same values).
AdzunaPreset = IngestSchedulePreset


@router.post("/discover", response_model=DiscoverJobsResponse)
async def discover_jobs_route(
    payload: DiscoverJobsRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> DiscoverJobsResponse:
    """Upsert jobs into the catalog (feed / connector → Postgres) and bootstrap scores for this user."""
    return await discover_upsert_jobs(session=session, user_id=user.id, payload=payload)


@router.post("/providers/adzuna/ingest", response_model=AdzunaIngestResponse)
async def ingest_adzuna_jobs_route(
    payload: AdzunaIngestRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> AdzunaIngestResponse:
    """Protected ingestion endpoint for Adzuna pages into the shared catalog."""
    adapter = AdzunaAdapter()
    result = await ingest_provider_jobs_paginated(
        session,
        user_id=user.id,
        adapter=adapter,
        base_params=ProviderFetchParams(
            keywords=payload.keywords,
            location=payload.location,
            country=payload.country,
            page=payload.start_page,
            per_page=payload.per_page,
        ),
        pages=payload.pages,
    )
    return AdzunaIngestResponse(**result)


@router.post("/providers/greenhouse/ingest", response_model=GreenhouseIngestResponse)
async def ingest_greenhouse_jobs_route(
    payload: GreenhouseIngestRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> GreenhouseIngestResponse:
    """Protected ingestion endpoint for Greenhouse boards into the shared catalog."""
    adapter = GreenhouseAdapter(board_tokens=payload.board_tokens)
    result = await ingest_provider_jobs_paginated(
        session,
        user_id=user.id,
        adapter=adapter,
        base_params=ProviderFetchParams(
            keywords=payload.keywords,
            location=payload.location,
            country=None,
            page=payload.start_page,
            per_page=payload.per_page,
        ),
        pages=payload.pages,
    )
    return GreenhouseIngestResponse(**result)


@router.post("/providers/greenhouse/ingest/preset", response_model=GreenhousePresetIngestResponse)
async def ingest_greenhouse_preset_route(
    preset: IngestSchedulePreset,
    keywords: str | None = Query(default=None, max_length=255),
    location: str | None = Query(default=None, max_length=255),
    start_page: int = Query(default=1, ge=1),
    boards: str | None = Query(
        default=None,
        max_length=512,
        description="Optional comma-separated Greenhouse board tokens (overrides GREENHOUSE_BOARD_TOKENS for this run).",
    ),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_authenticated_user),
) -> GreenhousePresetIngestResponse:
    """Cron-friendly Greenhouse ingestion: hourly/daily page depth from config; catalog system user actor."""
    try:
        pages, base_params = resolve_greenhouse_scheduled_ingest_params(
            settings,
            preset=preset.value,
            keywords=keywords,
            location=location,
            start_page=start_page,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    actor = settings.job_catalog_ingestion_user_id.strip()
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JOB_CATALOG_INGESTION_USER_ID is not configured",
        )

    tokens = settings.greenhouse_board_tokens_list()
    if boards and boards.strip():
        tokens = [p.strip() for p in boards.split(",") if p.strip()]
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GREENHOUSE_BOARD_TOKENS is empty (set env or pass boards=token1,token2)",
        )

    adapter = GreenhouseAdapter(board_tokens=tokens)
    result = await ingest_provider_jobs_paginated(
        session,
        user_id=actor,
        adapter=adapter,
        base_params=base_params,
        pages=pages,
    )
    return GreenhousePresetIngestResponse(
        **result,
        preset=preset.value,  # type: ignore[arg-type]
        catalog_actor_user_id=actor,
    )


@router.post("/providers/adzuna/ingest/preset", response_model=AdzunaPresetIngestResponse)
async def ingest_adzuna_preset_route(
    preset: IngestSchedulePreset,
    keywords: str | None = Query(default=None, max_length=255),
    location: str | None = Query(default=None, max_length=255),
    country: str | None = Query(default=None, max_length=8),
    start_page: int = Query(default=1, ge=1),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_authenticated_user),
) -> AdzunaPresetIngestResponse:
    """Cron-friendly ingestion: hourly/daily page depth from config; writes as catalog system user."""
    try:
        pages, base_params = resolve_adzuna_scheduled_ingest_params(
            settings,
            preset=preset.value,
            keywords=keywords,
            location=location,
            country=country,
            start_page=start_page,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    actor = settings.job_catalog_ingestion_user_id.strip()
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JOB_CATALOG_INGESTION_USER_ID is not configured",
        )

    adapter = AdzunaAdapter()
    result = await ingest_provider_jobs_paginated(
        session,
        user_id=actor,
        adapter=adapter,
        base_params=base_params,
        pages=pages,
    )
    return AdzunaPresetIngestResponse(
        **result,
        preset=preset.value,  # type: ignore[arg-type]
        catalog_actor_user_id=actor,
    )


@router.post("/providers/scrapling/ingest", response_model=ScraplingIngestResponse)
async def ingest_scrapling_jobs_route(
    payload: ScraplingIngestRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ScraplingIngestResponse:
    """Ingest jobs via Scrapling adapter (fixture bundle, explicit JSON path, or runtime hook when wired)."""
    if not settings.scrapling_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SCRAPLING_ENABLED is false; enable Scrapling in server configuration.",
        )
    result, run = await ingest_provider_jobs(
        session,
        user_id=user.id,
        adapter=ScraplingAdapter(settings),
        params=ProviderFetchParams(
            keywords=payload.keywords,
            location=payload.location,
            country=None,
            page=payload.page,
            per_page=payload.per_page,
        ),
    )
    deduped = int((run.metadata_json or {}).get("deduped_count") or 0)
    return ScraplingIngestResponse(
        created=int(result.created),
        updated=int(result.updated),
        run_ids=[str(run.id)],
        job_ids=[str(j) for j in result.job_ids],
        deduped=deduped,
    )


@router.post("/providers/catalog/ingest/preset", response_model=CatalogPresetIngestResponse)
async def ingest_catalog_multi_provider_preset_route(
    preset: IngestSchedulePreset,
    keywords: str | None = Query(default=None, max_length=255),
    location: str | None = Query(default=None, max_length=255),
    country: str | None = Query(default=None, max_length=8),
    start_page: int = Query(default=1, ge=1),
    resume_aligned: bool = Query(
        default=False,
        description="Merge keywords/location from the authenticated user's latest resume + preferences.",
    ),
    include_legacy_connectors: bool = Query(
        default=False,
        description="When true, runs legacy parallel connectors (Ashby, Lever, Remotive, …) with the same resume/query context.",
    ),
    include_scrapling: bool = Query(
        default=True,
        description="When true and SCRAPLING_ENABLED + SCRAPLING_CATALOG_IN_PRESET, runs Scrapling after Google Jobs.",
    ),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> CatalogPresetIngestResponse:
    """Unified catalog ingest: Adzuna → Greenhouse → Google Jobs → optional Scrapling → optional legacy connectors."""
    if not settings.job_catalog_ingestion_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JOB_CATALOG_INGESTION_USER_ID is not configured",
        )
    try:
        return await run_catalog_preset_ingest(
            session,
            settings,
            preset=preset.value,  # type: ignore[arg-type]
            user_id=user.id,
            keywords=keywords,
            location=location,
            country=country,
            start_page=start_page,
            resume_aligned=resume_aligned,
            include_legacy_connectors=include_legacy_connectors,
            include_scrapling=include_scrapling,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("", response_model=JobsListResponse)
async def list_jobs(
    min_fit: float = Query(default=0.0, ge=0.0, le=5.0),
    location: str | None = Query(default=None),
    has_salary: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> JobsListResponse:
    return await list_jobs_service(
        session=session,
        user_id=user.id,
        min_fit=min_fit,
        location=location,
        has_salary=has_salary,
        page=page,
    )


@router.post("/recompute-scores", response_model=JobScoresRecomputeResponse)
async def recompute_my_job_scores(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> JobScoresRecomputeResponse:
    refreshed = await recompute_job_scores_for_user(session, user.id)
    return JobScoresRecomputeResponse(user_id=user.id, refreshed_scores=refreshed)


@router.post(
    "/{job_id}/dismiss",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def dismiss_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> None:
    try:
        await dismiss_job_for_user(session=session, user_id=user.id, job_id=job_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from None
