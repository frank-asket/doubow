from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from config import settings


def _reject_private_target(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"portal_scanner: cannot resolve host {hostname}") from exc

    for info in infos:
        addr = info[4][0]
        ip = ipaddress.ip_address(addr)
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast:
            raise ValueError(f"portal_scanner: blocked private address target {addr}")


def _validate_source_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("portal_scanner: only http/https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("portal_scanner: URL hostname is required")
    if not settings.portal_scanner_allow_private_ips:
        _reject_private_target(parsed.hostname)
    return source_url


async def scan(source_url: str | None = None) -> list[dict]:
    """Return normalized discovery candidates. Empty list when no source configured."""
    if not source_url:
        return []
    url = _validate_source_url(source_url)
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, headers={"user-agent": "doubow-portal-scanner/1.0"})
        response.raise_for_status()
    # Current baseline scanner only validates safe reachability.
    # Structured parsing/connector extraction is implemented by dedicated discovery agents.
    return []
