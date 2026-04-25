"""Monitor agent — lightweight pipeline signals when callers pass ``applications`` context."""

from __future__ import annotations


class MonitorAgent:
    name = "monitor"

    async def run(self, context: dict) -> dict:
        changes: list[dict] = []
        apps = context.get("applications")
        if not isinstance(apps, list):
            return {"changes": []}
        for item in apps:
            if not isinstance(item, dict):
                continue
            app_id = item.get("id")
            if not isinstance(app_id, str):
                continue
            if item.get("is_stale") is True:
                changes.append(
                    {
                        "type": "stale_pipeline_row",
                        "application_id": app_id,
                        "reason": "Application flagged stale in pipeline store",
                    }
                )
            dedup = item.get("dedup_group")
            if isinstance(dedup, str) and dedup.strip():
                changes.append(
                    {
                        "type": "dedup_group",
                        "application_id": app_id,
                        "dedup_group": dedup.strip(),
                        "reason": "Application participates in a deduplication group",
                    }
                )
        return {"changes": changes}
