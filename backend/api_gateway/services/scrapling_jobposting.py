"""
Extract schema.org JobPosting records from HTML ``application/ld+json`` blocks.

Used by :mod:`scrapling_adapter` when no fixture path is configured. Fetching is done via
HTTP GET (``httpx``), with an optional ``scrapling.fetchers.Fetcher`` path when the heavy
``scrapling[fetchers]`` extra is installed.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_LD_JSON_SCRIPT_RE = re.compile(
    r'<script[^>]+type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def _is_http_url(url: str) -> bool:
    try:
        p = urlparse(url.strip())
    except Exception:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def _type_includes_job_posting(v: object) -> bool:
    if v == "JobPosting":
        return True
    if isinstance(v, list):
        return any(x == "JobPosting" for x in v if isinstance(x, str))
    return False


def _org_name(organization: object) -> str:
    if isinstance(organization, str):
        return organization.strip()
    if isinstance(organization, dict):
        name = organization.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return ""


def _org_logo(organization: object) -> str | None:
    if not isinstance(organization, dict):
        return None
    logo = organization.get("logo")
    if isinstance(logo, str) and logo.strip():
        return logo.strip()
    if isinstance(logo, dict):
        u = logo.get("url")
        if isinstance(u, str) and u.strip():
            return u.strip()
    return None


def _location_text(job_location: object) -> str | None:
    if job_location is None:
        return None
    if isinstance(job_location, str):
        t = job_location.strip()
        return t or None
    if isinstance(job_location, dict):
        if job_location.get("@type") == "Place" or "address" in job_location:
            addr = job_location.get("address")
            if isinstance(addr, str):
                return addr.strip() or None
            if isinstance(addr, dict):
                parts = [
                    addr.get("addressLocality"),
                    addr.get("addressRegion"),
                    addr.get("addressCountry"),
                ]
                joined = ", ".join(p for p in parts if isinstance(p, str) and p.strip())
                return joined or None
        name = job_location.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


def _as_jobposting_dict(node: dict[str, Any]) -> dict[str, Any] | None:
    if not _type_includes_job_posting(node.get("@type")):
        return None
    title = node.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    org = node.get("hiringOrganization")
    company = _org_name(org)
    if not company:
        return None

    raw_url = node.get("url") or node.get("sameAs")
    job_url = raw_url.strip() if isinstance(raw_url, str) else ""
    if not job_url or not _is_http_url(job_url):
        return None

    description = node.get("description")
    if isinstance(description, str):
        desc_str = description.strip()
    elif isinstance(description, dict):
        t = description.get("text")
        desc_str = t.strip() if isinstance(t, str) else ""
    else:
        desc_str = ""

    logo = _org_logo(org)
    loc = _location_text(node.get("jobLocation"))
    posted = node.get("datePosted") or node.get("dateposted")
    posted_str = posted.strip() if isinstance(posted, str) else None

    out: dict[str, Any] = {
        "title": title.strip()[:255],
        "company": company[:255],
        "url": job_url[:1000],
        "description": desc_str,
        "location": loc,
        "posted_at": posted_str,
    }
    if logo:
        out["logo_url"] = logo[:1000]
    return out


def _walk_json_ld(obj: Any, out: list[dict[str, Any]]) -> None:
    if isinstance(obj, dict):
        parsed = _as_jobposting_dict(obj)
        if parsed:
            out.append(parsed)
        graph = obj.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                _walk_json_ld(item, out)
        for k, v in obj.items():
            if k == "@graph":
                continue
            if isinstance(v, (dict, list)):
                _walk_json_ld(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _walk_json_ld(item, out)


def extract_jobposting_dicts_from_html(html: str, *, page_url: str) -> list[dict[str, Any]]:
    """
    Parse all ``application/ld+json`` scripts and collect JobPosting-shaped dicts
    compatible with :func:`scrapling_adapter.map_scrapling_record_to_discover_item`.
    """
    records: list[dict[str, Any]] = []
    for raw in _LD_JSON_SCRIPT_RE.findall(html):
        text = raw.strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.debug("ld+json parse skip on %s: %s", page_url, exc)
            continue
        _walk_json_ld(data, records)

    # De-dupe by job URL
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for r in records:
        u = str(r.get("url", ""))
        if u and u not in seen:
            seen.add(u)
            unique.append(r)
    return unique
