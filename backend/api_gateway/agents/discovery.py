"""Discovery agent — surfaces connector plan; catalog upsert uses ``POST /v1/jobs/discover``."""

from __future__ import annotations

from config import settings

KNOWN_JOB_SOURCES = frozenset(
    (
        "adzuna",
        "ashby",
        "catalog",
        "google_jobs",
        "greenhouse",
        "lever",
        "linkedin",
        "manual",
        "scrapling",
        "wellfound",
    ),
)


class DiscoveryAgent:
    name = "discovery"

    async def run(self, context: dict) -> dict:
        prefers = context.get("prefer_sources")
        plan: list[str] = []
        if isinstance(prefers, list):
            for item in prefers:
                if isinstance(item, str) and item in KNOWN_JOB_SOURCES and item not in plan:
                    plan.append(item)
        if not plan:
            plan = ["adzuna", "greenhouse", "google_jobs", "manual", "catalog"]
            if settings.scrapling_enabled:
                plan.insert(3, "scrapling")
        return {
            "jobs": [],
            "hint": _discovery_hint(),
            "connector_plan": plan,
        }


def _discovery_hint() -> str:
    base = (
        "Catalog ingest: POST /v1/jobs/providers/catalog/ingest/preset "
        "(resume_aligned=1, include_legacy_connectors=1 for full stack). "
        "Google Jobs needs SERPAPI_API_KEY. Legacy connectors respect the same query context when enabled."
    )
    if settings.scrapling_enabled:
        base += (
            " Scrapling runs when SCRAPLING_ENABLED and include_scrapling=true (also agent pipeline "
            "`run_job_search_pipeline` with catalog refresh). Runtime seeds: optional SCRAPLING_SEED_URLS "
            "plus, by default, job detail URLs from GREENHOUSE_BOARD_TOKENS (same boards as GreenhouseAdapter); "
            "or use JSON fixtures when not using live HTML."
        )
    return base
