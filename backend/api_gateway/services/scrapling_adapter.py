"""
Scrapling (D4Vinci/Scrapling) provider adapter — sketch for job catalog ingestion.

Repository: https://github.com/D4Vinci/Scrapling

This module does **not** require the heavy ``scrapling[fetchers]`` extra. It defines:

- A stable ``DiscoverJobItem`` mapping from normalized dicts (JSON fixture, JSON-LD HTML, or
  optional ``scrapling.fetchers.Fetcher`` when that extra is installed).
- **Runtime path**: ``httpx`` GET of ``SCRAPLING_SEED_URLS`` + ``application/ld+json`` JobPosting
  extraction (:mod:`scrapling_jobposting`). Optional Scrapling ``Fetcher.get`` is used first if importable.
- ``ScraplingAdapter`` implementing :class:`ProviderAdapter` (invoked via ``asyncio.to_thread``).

Configuration (see :class:`config.Settings`):

- ``SCRAPLING_ENABLED`` — master switch.
- ``SCRAPLING_FIXTURE_JSON_PATH`` — optional JSON path (overrides bundle).
- ``SCRAPLING_BUNDLE_FIXTURE`` — when true (default), load
  ``api_gateway/fixtures/scrapling_sample_jobs.json`` if no explicit path is set.
- ``SCRAPLING_SEED_URLS`` — optional extra pages to fetch for JSON-LD when no fixture is used.
- ``SCRAPLING_AUTO_GREENHOUSE_BOARD_SEEDS`` — when true (default), also adds job ``absolute_url``
  pages from ``GREENHOUSE_BOARD_TOKENS`` via the public Greenhouse Jobs API (aligned with catalog).

Expected record shape (flexible keys)::

    {
      "title": "Engineer",
      "company": "Acme",           // or company_name, employer
      "url": "https://...",       // or job_url, link
      "location": "Abidjan",
      "description": "...",
      "posted_at": "2025-01-15T00:00:00+00:00",
      "salary_range": "80k-100k",
      "logo_url": "https://...",
      "external_id": "optional"
    }

Fixture JSON may be either ``[{"title": ...}, ...]`` or ``{"jobs": [...]}`` /
``{"results": [...]}``.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from config import Settings, settings
from schemas.jobs import DiscoverJobItem
from services.job_ingestion_sanitizer import normalize_optional_http_url
from services.provider_adapter import ProviderAdapter, ProviderFetchParams, ProviderFetchResult
from services.scrapling_jobposting import extract_jobposting_dicts_from_html

logger = logging.getLogger(__name__)

PROVIDER_NAME = "scrapling"

_BUNDLED_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "scrapling_sample_jobs.json"


def resolve_scrapling_fixture_path(cfg: Settings) -> Path | None:
    """Prefer explicit path; else bundled sample jobs JSON when ``scrapling_bundle_fixture``."""
    explicit = (cfg.scrapling_fixture_json_path or "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"SCRAPLING_FIXTURE_JSON_PATH does not exist: {path}")
        return path
    if cfg.scrapling_bundle_fixture and _BUNDLED_FIXTURE.is_file():
        return _BUNDLED_FIXTURE
    return None


def _first_non_empty_str(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        val = data.get(key)
        if isinstance(val, str):
            text = val.strip()
            if text:
                return text
    return ""


def _parse_posted_at(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _stable_external_id(raw: dict[str, Any], *, url: str, title: str, company: str) -> str:
    explicit = _first_non_empty_str(raw, "external_id", "id", "job_id")
    if explicit:
        return explicit[:255]
    basis = f"{url}|{title}|{company}".encode("utf-8")
    digest = hashlib.sha256(basis).hexdigest()[:24]
    return f"scrapling-{digest}"


def map_scrapling_record_to_discover_item(
    raw: object,
    *,
    provider: str = PROVIDER_NAME,
) -> DiscoverJobItem | None:
    """
    Map one Scrapling-normalized dict to :class:`DiscoverJobItem`.

    Returns ``None`` if required fields (title, company) are missing.
    """
    if not isinstance(raw, dict):
        return None
    data = raw
    title = _first_non_empty_str(data, "title", "job_title", "name")
    company = _first_non_empty_str(data, "company", "company_name", "employer")
    if not title or not company:
        return None

    url_raw = data.get("url") or data.get("job_url") or data.get("link") or data.get("apply_url")
    url = normalize_optional_http_url(url_raw) or ""
    if not url:
        logger.warning(
            "scrapling record missing usable url; skipping title=%r company=%r",
            title[:80],
            company[:80],
        )
        return None

    description = _first_non_empty_str(
        data,
        "description",
        "description_raw",
        "text",
        "body",
        "content",
    )
    location = _first_non_empty_str(data, "location", "place", "city") or None
    salary_range = _first_non_empty_str(data, "salary_range", "salary") or None
    logo = normalize_optional_http_url(data.get("logo_url") or data.get("logo") or data.get("thumbnail"))
    posted_at = _parse_posted_at(data.get("posted_at") or data.get("date") or data.get("published_at"))
    external_id = _stable_external_id(data, url=url, title=title, company=company)

    return DiscoverJobItem(
        source=provider,
        external_id=external_id,
        title=title[:255],
        company=company[:255],
        location=location[:255] if location else None,
        salary_range=salary_range[:128] if salary_range else None,
        logo_url=logo,
        description_raw=description,
        description=description,
        url=url,
        posted_at=posted_at,
        score_template=None,
    )


def map_scrapling_batch(records: list[object], *, provider: str = PROVIDER_NAME) -> list[DiscoverJobItem]:
    """Map a list of dict records, skipping invalid entries."""
    out: list[DiscoverJobItem] = []
    for item in records:
        mapped = map_scrapling_record_to_discover_item(item, provider=provider)
        if mapped is not None:
            out.append(mapped)
    return out


def _load_fixture_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("jobs", "results", "records", "items"):
            inner = payload.get(key)
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
    raise ValueError(f"unsupported fixture JSON structure in {path}")


def _parse_seed_url_list(raw: str | None) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    out: list[str] = []
    for part in re.split(r"[\n,]", str(raw)):
        u = part.strip()
        if u:
            out.append(u)
    return out


def _fetch_greenhouse_job_detail_urls_for_scrapling(cfg: Settings) -> list[str]:
    """
    Use Doubow's configured ``GREENHOUSE_BOARD_TOKENS`` and the public Greenhouse Jobs API
    (same endpoint as :class:`GreenhouseAdapter`) to collect ``absolute_url`` job pages —
    those pages commonly embed schema.org JobPosting for Scrapling's HTML parser.
    """
    if not cfg.scrapling_auto_greenhouse_board_seeds:
        return []
    boards = cfg.greenhouse_board_tokens_list()
    if not boards:
        return []

    import httpx

    base = cfg.greenhouse_api_url.rstrip("/")
    per_board = max(1, min(50, int(cfg.scrapling_greenhouse_seed_jobs_per_board or 5)))
    timeout = max(5.0, min(float(cfg.scrapling_timeout_s or 60.0), 120.0))
    urls: list[str] = []
    with httpx.Client(timeout=timeout) as client:
        for token in boards:
            t = token.strip()
            if not t:
                continue
            endpoint = f"{base}/{t}/jobs"
            try:
                response = client.get(
                    endpoint,
                    params={"content": "true", "page": 1, "per_page": per_board},
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                logger.warning(
                    "scrapling: could not list Greenhouse jobs for board=%s (auto seed): %s",
                    t[:40],
                    exc,
                )
                continue
            jobs = payload.get("jobs") if isinstance(payload, dict) else None
            if not isinstance(jobs, list):
                continue
            for item in jobs:
                if not isinstance(item, dict):
                    continue
                raw_u = item.get("absolute_url")
                if isinstance(raw_u, str):
                    u = raw_u.strip()
                    if u.startswith(("http://", "https://")):
                        urls.append(u)
    return urls


def effective_scrapling_seed_urls(cfg: Settings) -> list[str]:
    """Explicit ``SCRAPLING_SEED_URLS`` first, then Greenhouse-derived job URLs (deduped)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for u in _parse_seed_url_list(cfg.scrapling_seed_urls):
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    for u in _fetch_greenhouse_job_detail_urls_for_scrapling(cfg):
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


def _http_get_text(url: str, timeout_s: float) -> str:
    """
    Fetch HTML. Prefer ``scrapling.fetchers.Fetcher`` when ``scrapling[fetchers]`` is installed;
    otherwise ``httpx`` (Alpine / minimal images).
    """
    try:
        from scrapling.fetchers import Fetcher  # type: ignore[import-untyped]

        resp = Fetcher.get(url, timeout=timeout_s, impersonate="chrome")
        text = getattr(resp, "text", None)
        if isinstance(text, str) and text:
            return text
    except Exception as exc:
        logger.debug("scrapling Fetcher.get failed for %s: %s; falling back to httpx", url, exc)

    import httpx

    with httpx.Client(timeout=timeout_s) as client:
        r = client.get(
            url,
            follow_redirects=True,
            headers={"User-Agent": "Doubow/1.0 (job catalog; +https://doubow.app)"},
        )
        r.raise_for_status()
        return r.text


def _invoke_scrapling_runtime(params: ProviderFetchParams, cfg: Settings) -> list[dict[str, Any]]:
    """
    Fetch seed URLs (explicit ``SCRAPLING_SEED_URLS`` + optional Greenhouse job pages from
    ``GREENHOUSE_BOARD_TOKENS``) and parse schema.org JobPosting from ``application/ld+json``.

    Returns dicts compatible with :func:`map_scrapling_record_to_discover_item`.
    """
    seed_urls = effective_scrapling_seed_urls(cfg)
    if not seed_urls:
        logger.info(
            "scrapling runtime: no seed URLs. Set SCRAPLING_SEED_URLS and/or "
            "GREENHOUSE_BOARD_TOKENS with SCRAPLING_AUTO_GREENHOUSE_BOARD_SEEDS=true, "
            "or use a JSON fixture / bundled sample."
        )
        return []

    timeout = max(1.0, min(float(cfg.scrapling_timeout_s or 60.0), 300.0))
    by_url: dict[str, dict[str, Any]] = {}
    for page_url in seed_urls:
        if not page_url.startswith(("http://", "https://")):
            logger.warning("scrapling runtime: skip non-http URL: %s", page_url[:80])
            continue
        try:
            html = _http_get_text(page_url, timeout)
        except Exception as exc:
            logger.warning("scrapling runtime: fetch failed %s: %s", page_url[:120], exc)
            continue
        for rec in extract_jobposting_dicts_from_html(html, page_url=page_url):
            u = str(rec.get("url", ""))
            if u and u not in by_url:
                by_url[u] = rec

    merged = list(by_url.values())
    merged.sort(key=lambda r: (r.get("company", ""), r.get("title", "")))

    kw = (params.keywords or "").strip().lower()
    if kw:
        merged = [
            r
            for r in merged
            if kw in str(r.get("title", "")).lower()
            or kw in str(r.get("company", "")).lower()
            or kw in str(r.get("description", "")).lower()
        ]

    loc_f = (params.location or "").strip().lower()
    if loc_f:
        merged = [
            r
            for r in merged
            if loc_f in str(r.get("location", "") or "").lower()
            or not str(r.get("location", "") or "").strip()
        ]

    per_page = max(1, min(100, int(params.per_page or 50)))
    page = max(1, int(params.page or 1))
    offset = (page - 1) * per_page
    return merged[offset : offset + per_page]


async def _fetch_raw_records(params: ProviderFetchParams, cfg: Settings) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = resolve_scrapling_fixture_path(cfg)
    if path is not None:

        def _load(p: Path = path) -> list[dict[str, Any]]:
            return _load_fixture_records(p)

        records = await asyncio.to_thread(_load)
        meta = {"mode": "fixture", "path": str(path), "count_raw": len(records)}
        return records, meta

    records = await asyncio.to_thread(_invoke_scrapling_runtime, params, cfg)
    return records, {"mode": "runtime", "count_raw": len(records)}


class ScraplingAdapter(ProviderAdapter):
    """Scrapling-backed :class:`ProviderAdapter` (optional; off by default)."""

    provider_name = PROVIDER_NAME

    def __init__(self, cfg: Settings | None = None) -> None:
        self._cfg = cfg or settings

    async def fetch_jobs(self, params: ProviderFetchParams) -> ProviderFetchResult:
        if not self._cfg.scrapling_enabled:
            return ProviderFetchResult(
                provider=self.provider_name,
                jobs=[],
                raw_records=[],
                metadata={"skipped": True, "reason": "scrapling_disabled"},
            )

        raw_list, fetch_meta = await _fetch_raw_records(params, self._cfg)

        jobs: list[DiscoverJobItem] = []
        raw_records: list[tuple[str, dict]] = []
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            item = map_scrapling_record_to_discover_item(raw, provider=self.provider_name)
            if item is None:
                continue
            jobs.append(item)
            raw_records.append((item.external_id, raw))

        meta = {
            **fetch_meta,
            "keywords": params.keywords,
            "location": params.location,
            "page": params.page,
            "count_normalized": len(jobs),
        }
        logger.info(
            "scrapling fetch provider=%s normalized=%s meta=%s",
            self.provider_name,
            len(jobs),
            fetch_meta.get("mode"),
        )
        return ProviderFetchResult(
            provider=self.provider_name,
            jobs=jobs,
            raw_records=raw_records,
            metadata=meta,
        )
