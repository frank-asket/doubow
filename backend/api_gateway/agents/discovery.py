"""Discovery agent — surfaces connector plan; catalog upsert uses ``POST /v1/jobs/discover``."""

from __future__ import annotations

KNOWN_JOB_SOURCES = frozenset(
    ("ashby", "greenhouse", "lever", "linkedin", "wellfound", "manual", "catalog"),
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
            plan = ["manual", "catalog"]
        return {
            "jobs": [],
            "hint": "Use POST /v1/jobs/discover to upsert catalog rows",
            "connector_plan": plan,
        }
