"""Discovery agent — surfaces connector plan; catalog upsert uses ``POST /v1/jobs/discover``."""

from __future__ import annotations

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
        return {
            "jobs": [],
            "hint": "Catalog ingest: POST /v1/jobs/providers/catalog/ingest/preset "
            "(resume_aligned=1, include_legacy_connectors=1 for full stack). "
            "Google Jobs needs SERPAPI_API_KEY. Legacy connectors respect the same query context when enabled.",
            "connector_plan": plan,
        }
