from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

from ingestion.connectors.base import BaseConnector, RawJob


class YCombinatorConnector(BaseConnector):
    source_name = "ycombinator"
    rate_limit_rps = 0.5

    async def fetch(self) -> AsyncIterator[RawJob]:
        try:
            response = await self._get("https://api.ycombinator.com/v0.1/jobs")
        except Exception:
            return
        payload = response.json()
        jobs = payload if isinstance(payload, list) else payload.get("jobs", [])
        if not isinstance(jobs, list):
            return
        for job in jobs:
            if not isinstance(job, dict):
                continue
            company = job.get("company") or {}
            location = str(job.get("location") or "")
            job_id = str(job.get("id") or job.get("slug") or "")
            if not job_id:
                continue
            yield RawJob(
                source=self.source_name,
                external_id=job_id,
                title=str(job.get("title", "")),
                company=str(company.get("name") or job.get("companyName") or ""),
                url=str(job.get("url") or f"https://www.workatastartup.com/jobs/{job_id}"),
                description=str(job.get("description") or job.get("body") or ""),
                location=location,
                remote=bool(job.get("remote")) or "remote" in location.lower(),
                posted_at=self._parse_date(job.get("createdAt") or job.get("posted_at")),
                tags=[str(t) for t in (job.get("tags") or [])][:10],
                department=str(job.get("department") or ""),
                extra={"yc_batch": str(company.get("batch") or "")},
            )

    @staticmethod
    def _parse_date(raw: object) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

