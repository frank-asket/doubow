from __future__ import annotations

from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx

from config import settings

if TYPE_CHECKING:
    from config import Settings
from schemas.jobs import DiscoverJobItem
from services.job_ingestion_sanitizer import normalize_optional_http_url
from services.provider_adapter import ProviderAdapter, ProviderFetchParams, ProviderFetchResult

logger = logging.getLogger(__name__)


def _parse_posted_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        # Adzuna date examples are usually ISO-like, sometimes ending with Z.
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _first_non_empty(*values: object) -> str:
    for item in values:
        if isinstance(item, str):
            text = item.strip()
            if text:
                return text
    return ""


def _logo_from_listing_url(url: str | None) -> str | None:
    normalized = normalize_optional_http_url(url)
    if not normalized:
        return None
    try:
        domain = (urlparse(normalized).hostname or "").strip().lower()
    except Exception:
        return None
    if not domain:
        return None
    return f"https://logo.clearbit.com/{domain}"


class AdzunaAdapter(ProviderAdapter):
    provider_name = "adzuna"

    def __init__(
        self,
        *,
        app_id: str | None = None,
        app_key: str | None = None,
        api_url: str | None = None,
        default_country: str | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        self._app_id = (app_id or settings.adzuna_app_id or "").strip()
        self._app_key = (app_key or settings.adzuna_app_key or "").strip()
        self._api_url = (api_url or settings.adzuna_api_url).rstrip("/")
        self._default_country = (default_country or settings.adzuna_country).strip().lower() or "gb"
        self._timeout_s = timeout_s

    async def fetch_jobs(self, params: ProviderFetchParams) -> ProviderFetchResult:
        if not self._app_id or not self._app_key:
            raise RuntimeError("Adzuna is not configured (ADZUNA_APP_ID and ADZUNA_APP_KEY are required)")

        country = (params.country or self._default_country or "gb").strip().lower()
        page = max(1, int(params.page or 1))
        per_page = max(1, min(50, int(params.per_page or settings.adzuna_results_per_page or 50)))
        endpoint = f"{self._api_url}/{country}/search/{page}"

        query: dict[str, Any] = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "results_per_page": per_page,
            "content-type": "application/json",
        }
        if params.keywords and params.keywords.strip():
            query["what"] = params.keywords.strip()
        if params.location and params.location.strip():
            query["where"] = params.location.strip()

        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            response = await client.get(endpoint, params=query)
            response.raise_for_status()
            payload = response.json()

        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raw_results = []

        jobs: list[DiscoverJobItem] = []
        raw_records: list[tuple[str, dict]] = []

        for item in raw_results:
            if not isinstance(item, dict):
                continue
            external_id = _first_non_empty(item.get("id"), item.get("redirect_url"))
            title = _first_non_empty(item.get("title"))
            company_name = _first_non_empty((item.get("company") or {}).get("display_name"))
            if not external_id or not title or not company_name:
                continue
            location_area = (item.get("location") or {}).get("area")
            location = ", ".join(str(v) for v in location_area if isinstance(v, str) and v.strip()) if isinstance(location_area, list) else ""
            canonical_url = normalize_optional_http_url(item.get("redirect_url")) or ""
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_range = None
            if isinstance(salary_min, (int, float)) or isinstance(salary_max, (int, float)):
                lo = f"{salary_min:.0f}" if isinstance(salary_min, (int, float)) else "?"
                hi = f"{salary_max:.0f}" if isinstance(salary_max, (int, float)) else "?"
                salary_range = f"{lo}-{hi}"
            description = _first_non_empty(item.get("description"))
            posted_at = _parse_posted_at(item.get("created"))

            jobs.append(
                DiscoverJobItem(
                    source=self.provider_name,
                    external_id=external_id,
                    title=title,
                    company=company_name,
                    location=location or None,
                    salary_range=salary_range,
                    logo_url=_logo_from_listing_url(canonical_url),
                    description_raw=description,
                    description=description,
                    url=canonical_url,
                    posted_at=posted_at,
                    score_template=None,
                )
            )
            raw_records.append((external_id, item))

        logger.info("adzuna fetched country=%s page=%s requested=%s accepted=%s", country, page, len(raw_results), len(jobs))

        return ProviderFetchResult(
            provider=self.provider_name,
            jobs=jobs,
            raw_records=raw_records,
            metadata={
                "country": country,
                "page": page,
                "requested_per_page": per_page,
                "count_returned": len(raw_results),
                "count_normalized": len(jobs),
            },
        )


def resolve_adzuna_scheduled_ingest_params(
    cfg: Settings,
    *,
    preset: str,
    keywords: str | None = None,
    location: str | None = None,
    country: str | None = None,
    start_page: int = 1,
) -> tuple[int, ProviderFetchParams]:
    """Resolve page depth and fetch params for hourly/daily cron-style ingestion."""
    key = (preset or "").strip().lower()
    if key == "hourly":
        pages = max(1, int(cfg.adzuna_ingest_hourly_pages))
    elif key == "daily":
        pages = max(1, int(cfg.adzuna_ingest_daily_pages))
    else:
        raise ValueError(f"invalid adzuna preset {preset!r}; expected hourly or daily")

    def _clean(v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    kw = _clean(keywords)
    if kw is None:
        kw = _clean(cfg.adzuna_ingest_default_keywords)
    loc = _clean(location)
    if loc is None:
        loc = _clean(cfg.adzuna_ingest_default_location)
    cnt_raw = _clean(country)
    cnt = cnt_raw if cnt_raw is not None else (cfg.adzuna_country or "gb").strip().lower() or "gb"
    per_page = max(1, min(50, int(cfg.adzuna_results_per_page)))
    page = max(1, int(start_page))

    return pages, ProviderFetchParams(
        keywords=kw,
        location=loc,
        country=cnt,
        page=page,
        per_page=per_page,
    )
