from __future__ import annotations

from urllib.parse import urlparse


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
    return raw

