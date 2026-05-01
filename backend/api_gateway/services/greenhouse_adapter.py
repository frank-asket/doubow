from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from typing import TYPE_CHECKING

from config import settings

if TYPE_CHECKING:
    from config import Settings
from schemas.jobs import DiscoverJobItem
from services.job_ingestion_sanitizer import normalize_optional_http_url
from services.provider_adapter import ProviderAdapter, ProviderFetchParams, ProviderFetchResult

logger = logging.getLogger(__name__)


def _first_non_empty(*values: object) -> str:
    for item in values:
        if isinstance(item, str):
            text = item.strip()
            if text:
                return text
    return ""


def _parse_posted_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


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


class GreenhouseAdapter(ProviderAdapter):
    provider_name = "greenhouse"

    def __init__(
        self,
        *,
        board_tokens: list[str] | None = None,
        api_url: str | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        from_config = settings.greenhouse_board_tokens_list()
        self._board_tokens = [b.strip() for b in (board_tokens or from_config) if b and b.strip()]
        self._api_url = (api_url or settings.greenhouse_api_url).rstrip("/")
        self._timeout_s = timeout_s

    async def fetch_jobs(self, params: ProviderFetchParams) -> ProviderFetchResult:
        if not self._board_tokens:
            raise RuntimeError("Greenhouse is not configured (set GREENHOUSE_BOARD_TOKENS)")

        page = max(1, int(params.page or 1))
        per_page = max(1, min(100, int(params.per_page or settings.greenhouse_results_per_page or 50)))
        kw = (params.keywords or "").strip().lower()
        loc_filter = (params.location or "").strip().lower()

        jobs: list[DiscoverJobItem] = []
        raw_records: list[tuple[str, dict]] = []
        fetched_total = 0

        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            for board in self._board_tokens:
                endpoint = f"{self._api_url}/{board}/jobs"
                response = await client.get(
                    endpoint,
                    params={"content": "true", "page": page, "per_page": per_page},
                )
                response.raise_for_status()
                payload = response.json()
                results = payload.get("jobs")
                if not isinstance(results, list):
                    results = []
                fetched_total += len(results)

                for item in results:
                    if not isinstance(item, dict):
                        continue
                    ext_id_raw = item.get("id")
                    title = _first_non_empty(item.get("title"))
                    if not title or ext_id_raw is None:
                        continue
                    absolute_url = normalize_optional_http_url(item.get("absolute_url")) or ""
                    company = _first_non_empty(board.replace("-", " ").title())
                    loc_name = _first_non_empty((item.get("location") or {}).get("name"))
                    description = _first_non_empty(item.get("content"))
                    posted_at = _parse_posted_at(item.get("updated_at") or item.get("created_at"))

                    # lightweight adapter-side filtering
                    haystack = f"{title}\n{description}".lower()
                    if kw and kw not in haystack:
                        continue
                    if loc_filter and loc_filter not in loc_name.lower():
                        continue

                    provider_job_id = f"{board}:{ext_id_raw}"
                    jobs.append(
                        DiscoverJobItem(
                            source=self.provider_name,
                            external_id=provider_job_id,
                            title=title,
                            company=company,
                            location=loc_name or None,
                            salary_range=None,
                            logo_url=_logo_from_listing_url(absolute_url),
                            description_raw=description,
                            description=description,
                            url=absolute_url,
                            posted_at=posted_at,
                            score_template=None,
                        )
                    )
                    raw_records.append((provider_job_id, item))

        logger.info(
            "greenhouse fetched boards=%s page=%s requested=%s accepted=%s",
            len(self._board_tokens),
            page,
            fetched_total,
            len(jobs),
        )

        return ProviderFetchResult(
            provider=self.provider_name,
            jobs=jobs,
            raw_records=raw_records,
            metadata={
                "boards": self._board_tokens,
                "page": page,
                "requested_per_page": per_page,
                "count_returned": fetched_total,
                "count_normalized": len(jobs),
            },
        )


def resolve_greenhouse_scheduled_ingest_params(
    cfg: "Settings",
    *,
    preset: str,
    keywords: str | None = None,
    location: str | None = None,
    start_page: int = 1,
) -> tuple[int, ProviderFetchParams]:
    """Resolve page depth and fetch params for hourly/daily Greenhouse cron-style ingestion."""
    key = (preset or "").strip().lower()
    if key == "hourly":
        pages = max(1, int(cfg.greenhouse_ingest_hourly_pages))
    elif key == "daily":
        pages = max(1, int(cfg.greenhouse_ingest_daily_pages))
    else:
        raise ValueError(f"invalid greenhouse preset {preset!r}; expected hourly or daily")

    def _clean(v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    kw = _clean(keywords)
    if kw is None:
        kw = _clean(cfg.greenhouse_ingest_default_keywords)
    loc = _clean(location)
    if loc is None:
        loc = _clean(cfg.greenhouse_ingest_default_location)

    per_page = max(1, min(100, int(cfg.greenhouse_results_per_page)))
    page = max(1, int(start_page))

    return pages, ProviderFetchParams(
        keywords=kw,
        location=loc,
        country=None,
        page=page,
        per_page=per_page,
    )
