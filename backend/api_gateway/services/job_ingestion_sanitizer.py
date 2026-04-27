from __future__ import annotations

from urllib.parse import urlparse, urlunparse


_HOST_REWRITES = {
    # Greenhouse listing URLs occasionally appear with this host, which can fail
    # DNS resolution in browsers for some users. Rewrite to the canonical board host.
    "job-boards.greenhouse.io": "boards.greenhouse.io",
}


def normalize_optional_http_url(value: object) -> str | None:
    """Return a normalized http(s) URL or None for malformed input."""
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        parsed = urlparse(raw)
    except Exception:
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    mapped_host = _HOST_REWRITES.get(host)
    if not mapped_host:
        return raw

    # Preserve path/query/fragment while swapping host.
    netloc = mapped_host
    if parsed.port:
        netloc = f"{mapped_host}:{parsed.port}"
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth = f"{auth}:{parsed.password}"
        netloc = f"{auth}@{netloc}"
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

