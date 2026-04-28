from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import AsyncIterator

from ingestion.connectors.base import BaseConnector, RawJob

DEFAULT_COMPANIES = ["openai", "cloudflare", "fastly", "github", "gitlab", "netlify"]


class LeverConnector(BaseConnector):
    source_name = "lever"
    rate_limit_rps = 2.0

    def __init__(self) -> None:
        super().__init__()
        extra = [v.strip() for v in os.getenv("LEVER_COMPANIES", "").split(",") if v.strip()]
        self.companies = list(dict.fromkeys(DEFAULT_COMPANIES + extra))

    async def fetch(self) -> AsyncIterator[RawJob]:
        for company in self.companies:
            try:
                response = await self._get(
                    f"https://api.lever.co/v0/postings/{company}",
                    params={"mode": "json", "limit": "250"},
                )
            except Exception:
                continue
            jobs = response.json()
            if not isinstance(jobs, list):
                continue
            for job in jobs:
                if not isinstance(job, dict):
                    continue
                categories = job.get("categories") or {}
                location = str(categories.get("location") or "")
                yield RawJob(
                    source=self.source_name,
                    external_id=str(job.get("id", "")),
                    title=str(job.get("text", "")),
                    company=company.replace("-", " ").title(),
                    url=str(job.get("hostedUrl", f"https://jobs.lever.co/{company}")),
                    description=str(job.get("descriptionPlain") or job.get("description") or ""),
                    location=location,
                    remote="remote" in location.lower(),
                    posted_at=self._parse_epoch_ms(job.get("createdAt")),
                    department=str(categories.get("department") or categories.get("team") or ""),
                    employment_type=self._employment_type(str(categories.get("commitment") or "")),
                    extra={"company": company},
                )

    @staticmethod
    def _parse_epoch_ms(raw: object) -> datetime | None:
        if raw is None:
            return None
        try:
            return datetime.fromtimestamp(int(raw) / 1000, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None

    @staticmethod
    def _employment_type(raw: str) -> str:
        lower = raw.lower()
        if "part" in lower:
            return "part_time"
        if "contract" in lower:
            return "contract"
        if "intern" in lower:
            return "internship"
        return "full_time"

