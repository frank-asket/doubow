"""Google Jobs listings via SerpAPI (optional third-party; subject to plan limits and their ToS)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import httpx

from config import settings
from schemas.jobs import DiscoverJobItem
from services.job_ingestion_sanitizer import normalize_optional_http_url
from services.provider_adapter import ProviderAdapter, ProviderFetchParams, ProviderFetchResult

logger = logging.getLogger(__name__)

_SERPAPI_SEARCH = "https://serpapi.com/search.json"


class SerpApiGoogleJobsAdapter(ProviderAdapter):
    """Fetches Google Jobs vertical results through SerpAPI's ``engine=google_jobs``."""

    provider_name = "google_jobs"

    def __init__(self, *, timeout_s: float = 30.0) -> None:
        self._timeout_s = timeout_s

    async def fetch_jobs(self, params: ProviderFetchParams) -> ProviderFetchResult:
        if not (settings.serpapi_api_key or "").strip():
            raise RuntimeError("SERPAPI_API_KEY is not configured")

        q = (params.keywords or settings.google_jobs_default_query or "").strip()
        if not q:
            q = "software engineer"
        loc = (params.location or "").strip() or None

        jobs: list[DiscoverJobItem] = []
        raw_records: list[tuple[str, dict]] = []
        next_token: str | None = None
        max_rounds = max(1, min(10, int(settings.google_jobs_serp_max_rounds)))

        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            for round_i in range(max_rounds):
                payload = await self._one_request(client, q=q, location=loc, next_page_token=next_token)
                batch = payload.get("jobs_results") if isinstance(payload, dict) else None
                if not isinstance(batch, list):
                    batch = []
                for item in batch:
                    if not isinstance(item, dict):
                        continue
                    dj, pid = self._map_row(item)
                    if dj is None:
                        continue
                    jobs.append(dj)
                    raw_records.append((pid, item))

                pag = (payload or {}).get("serpapi_pagination") if isinstance(payload, dict) else None
                next_token = None
                if isinstance(pag, dict):
                    next_token = pag.get("next_page_token")
                    if isinstance(next_token, str) and next_token.strip():
                        next_token = next_token.strip()
                    else:
                        next_token = None
                if not next_token:
                    break
                if round_i == 0 and not batch:
                    break

        return ProviderFetchResult(
            provider=self.provider_name,
            jobs=jobs,
            raw_records=raw_records,
            metadata={
                "query": q,
                "location": loc,
                "rounds": max_rounds,
                "count": len(jobs),
            },
        )

    async def _one_request(
        self,
        client: httpx.AsyncClient,
        *,
        q: str,
        location: str | None,
        next_page_token: str | None,
    ) -> dict[str, Any]:
        api_key = (settings.serpapi_api_key or "").strip()
        params: dict[str, Any] = {
            "engine": "google_jobs",
            "api_key": api_key,
            "q": q,
            "hl": (settings.google_jobs_hl or "en").strip() or "en",
        }
        if location:
            params["location"] = location
        gl = (settings.google_jobs_gl or "").strip()
        if gl:
            params["gl"] = gl
        if next_page_token:
            params["next_page_token"] = next_page_token
        r = await client.get(_SERPAPI_SEARCH, params=params)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            return {}
        err = data.get("error")
        if err:
            logger.warning("serpapi google_jobs error: %s", err)
        return data

    def _map_row(self, item: dict[str, Any]) -> tuple[DiscoverJobItem | None, str]:
        title = str(item.get("title") or "").strip()
        company = str(item.get("company_name") or "").strip()
        if not title or not company:
            return None, ""
        loc = str(item.get("location") or "").strip() or None
        desc = str(item.get("description") or "").strip()
        share = str(item.get("share_link") or "").strip()
        jid_raw = item.get("job_id")
        jid = str(jid_raw).strip() if isinstance(jid_raw, str) else ""
        ext = hashlib.sha256(f"{jid}|{share}|{title}|{company}".encode()).hexdigest()[:32]
        url = share
        apply_opts = item.get("apply_options")
        if isinstance(apply_opts, list) and apply_opts:
            first = apply_opts[0]
            if isinstance(first, dict):
                link = normalize_optional_http_url(first.get("link"))
                if link:
                    url = link
        if not url:
            url = share
        url = normalize_optional_http_url(url) or ""
        thumb = normalize_optional_http_url(item.get("thumbnail"))

        dj = DiscoverJobItem(
            source=self.provider_name,
            external_id=ext,
            title=title,
            company=company,
            location=loc,
            salary_range=None,
            logo_url=thumb,
            description_raw=desc,
            description=desc,
            url=url or share or "https://www.google.com/search?udm=8&q=jobs",
            posted_at=None,
            score_template=None,
        )
        return dj, ext
