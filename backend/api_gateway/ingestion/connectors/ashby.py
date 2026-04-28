from __future__ import annotations

import os
from datetime import datetime
from typing import AsyncIterator

from ingestion.connectors.base import BaseConnector, RawJob

DEFAULT_ORGS = ["cohere", "mistral", "together-ai", "modal-labs", "langfuse", "sourcegraph"]


class AshbyConnector(BaseConnector):
    source_name = "ashby"
    rate_limit_rps = 1.0

    def __init__(self) -> None:
        super().__init__()
        extra = [v.strip() for v in os.getenv("ASHBY_ORG_SLUGS", "").split(",") if v.strip()]
        self.orgs = list(dict.fromkeys(DEFAULT_ORGS + extra))

    async def fetch(self) -> AsyncIterator[RawJob]:
        if self._client is None:
            raise RuntimeError("HTTP client not initialized")
        for slug in self.orgs:
            try:
                await self._rate_limit()
                response = await self._client.post(
                    f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                    json={"includeCompensation": True},
                )
                if response.status_code == 404:
                    continue
                response.raise_for_status()
            except Exception:
                continue
            data = response.json()
            postings = data.get("jobPostings") if isinstance(data, dict) else []
            if not isinstance(postings, list):
                continue
            company = ((data.get("organization") or {}).get("name") or slug.replace("-", " ").title()).strip()
            for job in postings:
                if not isinstance(job, dict):
                    continue
                comp = job.get("compensation") or {}
                yield RawJob(
                    source=self.source_name,
                    external_id=str(job.get("id", "")),
                    title=str(job.get("title", "")),
                    company=company,
                    url=str(job.get("jobPostingUrl", f"https://jobs.ashbyhq.com/{slug}")),
                    description=str(job.get("descriptionHtml") or job.get("descriptionPlain") or ""),
                    location=self._format_location(job.get("primaryLocation") or {}),
                    remote=str(job.get("workplaceType", "")).lower() in {"remote", "hybrid"},
                    salary_min=self._maybe_int(comp.get("minValue")),
                    salary_max=self._maybe_int(comp.get("maxValue")),
                    currency=str(comp.get("currency") or "USD"),
                    posted_at=self._parse_date(job.get("publishedAt")),
                    department=((job.get("department") or {}).get("name") or ""),
                    employment_type=self._employment_type(str(job.get("employmentType", ""))),
                    extra={"slug": slug},
                )

    @staticmethod
    def _format_location(loc: dict) -> str:
        if not isinstance(loc, dict):
            return ""
        return ", ".join(str(loc.get(k, "")).strip() for k in ("city", "region", "country") if loc.get(k))

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

    @staticmethod
    def _parse_date(raw: object) -> datetime | None:
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _maybe_int(raw: object) -> int | None:
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

