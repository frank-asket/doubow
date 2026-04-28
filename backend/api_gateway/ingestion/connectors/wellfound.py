from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from typing import AsyncIterator

from ingestion.connectors.base import BaseConnector, RawJob

SEARCH_QUERIES = [
    "machine learning engineer",
    "ai engineer",
    "llm engineer",
    "mlops",
    "data scientist",
    "backend engineer",
]


class WellfoundConnector(BaseConnector):
    source_name = "wellfound"
    rate_limit_rps = 0.5

    def __init__(self) -> None:
        super().__init__()
        self.token = os.getenv("WELLFOUND_API_TOKEN", "").strip()

    async def fetch(self) -> AsyncIterator[RawJob]:
        if self.token:
            async for job in self._fetch_authenticated():
                yield job
            return
        async for job in self._fetch_public():
            yield job

    async def _fetch_authenticated(self) -> AsyncIterator[RawJob]:
        if self._client is None:
            raise RuntimeError("HTTP client not initialized")
        query = """
        query JobListings($query: String!, $page: Int!) {
          jobListings(query: $query, page: $page, per_page: 50) {
            jobListings {
              id
              title
              description
              remote
              locationNames
              jobType
              salary
              createdAt
              applyUrl
              startup { name }
              tags { displayName }
            }
            totalJobListings
          }
        }
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        for search in SEARCH_QUERIES:
            page = 1
            while page <= 5:
                try:
                    await self._rate_limit()
                    response = await self._client.post(
                        "https://api.wellfound.com/graphql",
                        json={"query": query, "variables": {"query": search, "page": page}},
                        headers=headers,
                    )
                    response.raise_for_status()
                except Exception:
                    break
                payload = response.json()
                listings = (((payload.get("data") or {}).get("jobListings") or {}).get("jobListings") or [])
                if not listings:
                    break
                for listing in listings:
                    if not isinstance(listing, dict):
                        continue
                    mapped = self._map_listing(listing)
                    if mapped:
                        yield mapped
                page += 1

    async def _fetch_public(self) -> AsyncIterator[RawJob]:
        for slug in [
            "machine-learning-engineer",
            "software-engineer",
            "data-scientist",
            "ai-engineer",
            "backend-engineer",
        ]:
            try:
                response = await self._get(
                    f"https://wellfound.com/role/l/{slug}",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; doubow-ingestion/1.0)"},
                    follow_redirects=True,
                )
            except Exception:
                continue
            scripts = re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                response.text,
                flags=re.DOTALL,
            )
            for raw in scripts:
                try:
                    parsed = json.loads(raw.strip())
                except Exception:
                    continue
                if isinstance(parsed, list):
                    for item in parsed:
                        mapped = self._map_jsonld(item)
                        if mapped:
                            yield mapped
                else:
                    mapped = self._map_jsonld(parsed)
                    if mapped:
                        yield mapped

    def _map_listing(self, listing: dict) -> RawJob | None:
        title = str(listing.get("title", "")).strip()
        url = str(listing.get("applyUrl", "")).strip()
        if not title or not url:
            return None
        startup = listing.get("startup") or {}
        location_names = listing.get("locationNames") or []
        location = ", ".join([str(v) for v in location_names[:2] if v])
        salary_text = str(listing.get("salary") or "")
        numbers = re.findall(r"[\d,]+", salary_text)
        salary_min = salary_max = None
        if len(numbers) >= 2:
            salary_min = self._maybe_int(numbers[0].replace(",", ""))
            salary_max = self._maybe_int(numbers[1].replace(",", ""))
        return RawJob(
            source=self.source_name,
            external_id=str(listing.get("id", "")),
            title=title,
            company=str(startup.get("name") or "Unknown"),
            url=url,
            description=str(listing.get("description", "")),
            location=location,
            remote=bool(listing.get("remote")) or "remote" in location.lower(),
            salary_min=salary_min,
            salary_max=salary_max,
            currency="USD",
            posted_at=self._parse_date(listing.get("createdAt")),
            tags=[str(t.get("displayName")) for t in (listing.get("tags") or []) if isinstance(t, dict) and t.get("displayName")],
            employment_type=self._employment_type(str(listing.get("jobType", ""))),
        )

    def _map_jsonld(self, item: object) -> RawJob | None:
        if not isinstance(item, dict) or item.get("@type") != "JobPosting":
            return None
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        description = str(item.get("description", "")).strip()
        if not title or not url:
            return None
        hiring_org = item.get("hiringOrganization") or {}
        ext_id = hashlib.md5(url.encode()).hexdigest()[:16]
        return RawJob(
            source=self.source_name,
            external_id=ext_id,
            title=title,
            company=str((hiring_org or {}).get("name") or "Unknown"),
            url=url,
            description=description,
            location="",
            remote=str(item.get("jobLocationType") or "").upper() == "TELECOMMUTE",
            posted_at=self._parse_date(item.get("datePosted")),
            tags=[],
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

    @staticmethod
    def _maybe_int(raw: str) -> int | None:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

