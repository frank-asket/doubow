from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

from ingestion.connectors.base import BaseConnector, RawJob

TARGET_CATEGORIES = ["software-dev", "data", "devops", "product", "qa"]


class RemotiveConnector(BaseConnector):
    source_name = "remotive"
    rate_limit_rps = 1.0

    async def fetch(self) -> AsyncIterator[RawJob]:
        for category in TARGET_CATEGORIES:
            try:
                response = await self._get(
                    "https://remotive.com/api/remote-jobs",
                    params={"category": category, "limit": "100"},
                )
            except Exception:
                continue
            payload = response.json()
            jobs = payload.get("jobs") if isinstance(payload, dict) else []
            if not isinstance(jobs, list):
                continue
            for job in jobs:
                if not isinstance(job, dict):
                    continue
                yield RawJob(
                    source=self.source_name,
                    external_id=str(job.get("id", "")),
                    title=str(job.get("title", "")),
                    company=str(job.get("company_name", "")),
                    url=str(job.get("url", "")),
                    description=str(job.get("description", "")),
                    location="Remote",
                    remote=True,
                    posted_at=self._parse_date(job.get("publication_date")),
                    tags=[str(t) for t in (job.get("tags") or [])][:10],
                    department=str(job.get("category", "")),
                    employment_type=self._employment_type(str(job.get("job_type", ""))),
                    extra={"category": category},
                )

    @staticmethod
    def _parse_date(raw: object) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
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

