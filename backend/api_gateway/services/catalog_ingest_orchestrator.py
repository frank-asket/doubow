"""Single orchestration entry for multi-provider + legacy connector catalog ingestion."""

from __future__ import annotations

import logging
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from schemas.jobs import CatalogPresetIngestResponse, ProviderIngestSummary
from services.adzuna_adapter import AdzunaAdapter, resolve_adzuna_scheduled_ingest_params
from services.connector_catalog_bootstrap import ensure_score_templates_for_legacy_connector_jobs
from services.greenhouse_adapter import GreenhouseAdapter
from services.job_provider_ingestion_service import ingest_provider_jobs, ingest_provider_jobs_paginated
from services.provider_adapter import ProviderFetchParams
from services.resume_catalog_params import merge_catalog_params_with_resume
from services.scrapling_adapter import ScraplingAdapter
from services.serpapi_google_jobs_adapter import SerpApiGoogleJobsAdapter

logger = logging.getLogger(__name__)


async def run_catalog_preset_ingest(
    session: AsyncSession,
    settings: Settings,
    *,
    preset: Literal["hourly", "daily"],
    user_id: str,
    keywords: str | None,
    location: str | None,
    country: str | None,
    start_page: int,
    resume_aligned: bool,
    include_legacy_connectors: bool = False,
    include_scrapling: bool = True,
) -> CatalogPresetIngestResponse:
    """Adzuna → Greenhouse (adapter) → Google Jobs (SerpAPI) → optional Scrapling → optional legacy connectors + template backfill."""

    pages, base_params = resolve_adzuna_scheduled_ingest_params(
        settings,
        preset=preset,
        keywords=keywords,
        location=location,
        country=country,
        start_page=start_page,
    )

    if resume_aligned:
        base_params = await merge_catalog_params_with_resume(session, user_id, base_params)

    actor = settings.job_catalog_ingestion_user_id.strip()

    provider_summaries: list[ProviderIngestSummary] = []
    job_ids: list[str] = []
    run_ids: list[str] = []
    created = 0
    updated = 0
    deduped = 0

    # 1) Adzuna
    try:
        adzuna_result = await ingest_provider_jobs_paginated(
            session,
            user_id=actor,
            adapter=AdzunaAdapter(),
            base_params=base_params,
            pages=pages,
        )
        provider_summaries.append(
            ProviderIngestSummary(
                provider="adzuna",
                status="completed",
                pages=int(adzuna_result["pages"]),
                created=int(adzuna_result["created"]),
                updated=int(adzuna_result["updated"]),
                deduped=int(adzuna_result.get("deduped", 0) or 0),
                run_ids=[str(r) for r in adzuna_result["run_ids"]],
            )
        )
        created += int(adzuna_result["created"])
        updated += int(adzuna_result["updated"])
        deduped += int(adzuna_result.get("deduped", 0) or 0)
        job_ids.extend([str(j) for j in adzuna_result["job_ids"]])
        run_ids.extend([str(r) for r in adzuna_result["run_ids"]])
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("catalog ingest: adzuna failed")
        provider_summaries.append(
            ProviderIngestSummary(
                provider="adzuna",
                status="failed",
                pages=pages,
                error=str(exc)[:500],
            )
        )

    # 2) Greenhouse (HTTP adapter path; distinct from legacy GreenhouseConnector)
    greenhouse_tokens = settings.greenhouse_board_tokens_list()
    if greenhouse_tokens:
        try:
            greenhouse_result = await ingest_provider_jobs_paginated(
                session,
                user_id=actor,
                adapter=GreenhouseAdapter(board_tokens=greenhouse_tokens),
                base_params=ProviderFetchParams(
                    keywords=base_params.keywords,
                    location=base_params.location,
                    country=None,
                    page=base_params.page,
                    per_page=base_params.per_page,
                    posted_after=base_params.posted_after,
                ),
                pages=pages,
            )
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="greenhouse",
                    status="completed",
                    pages=int(greenhouse_result["pages"]),
                    created=int(greenhouse_result["created"]),
                    updated=int(greenhouse_result["updated"]),
                    deduped=int(greenhouse_result.get("deduped", 0) or 0),
                    run_ids=[str(r) for r in greenhouse_result["run_ids"]],
                )
            )
            created += int(greenhouse_result["created"])
            updated += int(greenhouse_result["updated"])
            deduped += int(greenhouse_result.get("deduped", 0) or 0)
            job_ids.extend([str(j) for j in greenhouse_result["job_ids"]])
            run_ids.extend([str(r) for r in greenhouse_result["run_ids"]])
        except Exception as exc:  # pragma: no cover
            logger.exception("catalog ingest: greenhouse adapter failed")
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="greenhouse",
                    status="failed",
                    pages=pages,
                    error=str(exc)[:500],
                )
            )
    else:
        provider_summaries.append(
            ProviderIngestSummary(
                provider="greenhouse",
                status="skipped",
                pages=0,
                error="GREENHOUSE_BOARD_TOKENS is empty; provider skipped.",
            )
        )

    # 3) Google Jobs (SerpAPI)
    if (settings.serpapi_api_key or "").strip():
        try:
            gj_result, gj_run = await ingest_provider_jobs(
                session,
                user_id=actor,
                adapter=SerpApiGoogleJobsAdapter(),
                params=ProviderFetchParams(
                    keywords=base_params.keywords,
                    location=base_params.location,
                    country=base_params.country,
                    page=max(1, int(base_params.page)),
                    per_page=base_params.per_page,
                    posted_after=base_params.posted_after,
                ),
            )
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="google_jobs",
                    status="completed",
                    pages=1,
                    created=int(gj_result.created),
                    updated=int(gj_result.updated),
                    deduped=0,
                    run_ids=[str(gj_run.id)],
                )
            )
            created += int(gj_result.created)
            updated += int(gj_result.updated)
            job_ids.extend([str(j) for j in gj_result.job_ids])
            run_ids.append(str(gj_run.id))
        except Exception as exc:  # pragma: no cover
            logger.exception("catalog ingest: google_jobs failed")
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="google_jobs",
                    status="failed",
                    pages=1,
                    error=str(exc)[:500],
                )
            )
    else:
        provider_summaries.append(
            ProviderIngestSummary(
                provider="google_jobs",
                status="skipped",
                pages=0,
                error="SERPAPI_API_KEY is not set; Google Jobs ingest skipped.",
            )
        )

    # 4) Scrapling (fixture or runtime hook; requires SCRAPLING_ENABLED)
    want_scrapling = (
        bool(include_scrapling)
        and bool(settings.scrapling_catalog_in_preset)
        and bool(settings.scrapling_enabled)
    )
    if want_scrapling:
        try:
            sl_result, sl_run = await ingest_provider_jobs(
                session,
                user_id=actor,
                adapter=ScraplingAdapter(settings),
                params=ProviderFetchParams(
                    keywords=base_params.keywords,
                    location=base_params.location,
                    country=base_params.country,
                    page=max(1, int(base_params.page)),
                    per_page=max(1, min(50, int(base_params.per_page or 50))),
                    posted_after=base_params.posted_after,
                ),
            )
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="scrapling",
                    status="completed",
                    pages=1,
                    created=int(sl_result.created),
                    updated=int(sl_result.updated),
                    deduped=0,
                    run_ids=[str(sl_run.id)],
                )
            )
            created += int(sl_result.created)
            updated += int(sl_result.updated)
            job_ids.extend([str(j) for j in sl_result.job_ids])
            run_ids.append(str(sl_run.id))
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("catalog ingest: scrapling failed")
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="scrapling",
                    status="failed",
                    pages=1,
                    error=str(exc)[:500],
                )
            )
    else:
        skip_reason: str
        if not include_scrapling:
            skip_reason = "include_scrapling=false on this request."
        elif not settings.scrapling_catalog_in_preset:
            skip_reason = "SCRAPLING_CATALOG_IN_PRESET is false."
        elif not settings.scrapling_enabled:
            skip_reason = "SCRAPLING_ENABLED is false; set env to ingest fixture/runtime output."
        else:
            skip_reason = "Scrapling skipped."
        provider_summaries.append(
            ProviderIngestSummary(
                provider="scrapling",
                status="skipped",
                pages=0,
                error=skip_reason,
            )
        )

    # 5) Legacy parallel connectors (Ashby, Lever, Remotive, …) — same resume keywords/location filter
    if include_legacy_connectors:
        try:
            from ingestion.scheduler.ingestion_engine import run_ingestion

            ing_summary = await run_ingestion(session, fetch_context=base_params)
            lc_err = None
            if ing_summary.total_errors:
                lc_err = (
                    f"{ing_summary.total_errors} connector error(s); "
                    f"inserted={ing_summary.total_inserted} see ingestion_runs / ingestion_engine logs."
                )
            lc_status = "completed"
            if ing_summary.total_inserted == 0 and ing_summary.total_errors > 0:
                lc_status = "failed"
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="legacy_connectors",
                    status=lc_status,
                    pages=1,
                    created=int(ing_summary.total_inserted),
                    updated=0,
                    deduped=int(ing_summary.total_dupes),
                    run_ids=[ing_summary.run_id],
                    error=lc_err,
                )
            )
            created += int(ing_summary.total_inserted)
            deduped += int(ing_summary.total_dupes)
        except Exception as exc:  # pragma: no cover
            logger.exception("catalog ingest: legacy connectors failed")
            provider_summaries.append(
                ProviderIngestSummary(
                    provider="legacy_connectors",
                    status="failed",
                    pages=0,
                    error=str(exc)[:500],
                )
            )

        try:
            await ensure_score_templates_for_legacy_connector_jobs(session)
            await session.commit()
        except Exception:  # pragma: no cover
            logger.exception("catalog ingest: score_template backfill failed")
            await session.rollback()

    completed = sum(1 for p in provider_summaries if p.status == "completed")
    failed = sum(1 for p in provider_summaries if p.status == "failed")
    if completed > 0 and failed == 0:
        overall_status = "ok"
    elif completed > 0:
        overall_status = "partial"
    else:
        overall_status = "failed"

    return CatalogPresetIngestResponse(
        preset=preset,  # type: ignore[arg-type]
        catalog_actor_user_id=actor,
        status=overall_status,  # type: ignore[arg-type]
        providers=provider_summaries,
        created=created,
        updated=updated,
        deduped=deduped,
        run_ids=run_ids,
        job_ids=job_ids,
    )
