"""Discovery stub — real ingestion uses ``POST /v1/jobs/discover`` (see ``job_discovery_service``)."""


class DiscoveryAgent:
    name = "discovery"

    async def run(self, context: dict) -> dict:
        _ = context
        return {"jobs": [], "hint": "Use POST /v1/jobs/discover to upsert catalog rows"}
