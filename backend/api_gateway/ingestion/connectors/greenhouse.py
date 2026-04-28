from __future__ import annotations

import os
from datetime import datetime
from typing import AsyncIterator

from ingestion.connectors.base import BaseConnector, RawJob

DEFAULT_TOKENS = [
    "openai",
    "anthropic",
    "cohere",
    "mistral",
    "databricks",
    "vercel",
    "supabase",
    "neon",
    "linear",
    "figma",
    "notion",
]


class GreenhouseConnector(BaseConnector):
    source_name = "greenhouse"
    rate_limit_rps = 2.0

    def __init__(self) -> None:
        super().__init__()
        override = os.getenv("GREENHOUSE_BOARD_TOKENS", "").strip()
        extra = [v.strip() for v in os.getenv("GREENHOUSE_EXTRA_TOKENS", "").split(",") if v.strip()]
        base = [v.strip() for v in override.split(",") if v.strip()] if override else DEFAULT_TOKENS
        self.tokens = list(dict.fromkeys(base + extra))

    async def fetch(self) -> AsyncIterator[RawJob]:
        for token in self.tokens:
            try:
                response = await self._get(
                    f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
                    params={"content": "true"},
                )
            except Exception:
                continue
            payload = response.json()
            jobs = payload.get("jobs") if isinstance(payload, dict) else []
            if not isinstance(jobs, list):
                continue
            for item in jobs:
                if not isinstance(item, dict):
                    continue
                location = ((item.get("location") or {}).get("name") or "").strip()
                yield RawJob(
                    source=self.source_name,
                    external_id=str(item.get("id", "")),
                    title=str(item.get("title", "")),
                    company=str(payload.get("name", token.replace("-", " ").title())),
                    url=str(item.get("absolute_url", f"https://boards.greenhouse.io/{token}")),
                    description=str(item.get("content") or item.get("absolute_url") or ""),
                    location=location,
                    remote="remote" in location.lower(),
                    posted_at=self._parse_date(item.get("updated_at") or item.get("created_at")),
                    tags=[o.get("name", "") for o in (item.get("offices") or []) if isinstance(o, dict) and o.get("name")],
                    department=((item.get("departments") or [{}])[0] or {}).get("name", ""),
                    extra={"token": token},
                )

    @staticmethod
    def _parse_date(raw: object) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

