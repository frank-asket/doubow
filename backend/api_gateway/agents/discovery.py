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
            "hint": "Catalog ingest: POST /v1/jobs/providers/catalog/ingest/preset (optional resume_aligned=1). "
            "Google Jobs requires SERPAPI_API_KEY (third-party; plan limits apply).",
            "connector_plan": plan,
        }
