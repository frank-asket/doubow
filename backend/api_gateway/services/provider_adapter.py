from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from schemas.jobs import DiscoverJobItem


@dataclass(slots=True)
class ProviderFetchParams:
    """Normalized query surface for third-party job providers."""

    keywords: str | None = None
    location: str | None = None
    country: str | None = None
    page: int = 1
    per_page: int = 50
    posted_after: datetime | None = None


@dataclass(slots=True)
class ProviderFetchResult:
    provider: str
    jobs: list[DiscoverJobItem]
    raw_records: list[tuple[str, dict]]
    metadata: dict


class ProviderAdapter(Protocol):
    provider_name: str

    async def fetch_jobs(self, params: ProviderFetchParams) -> ProviderFetchResult:
        """Fetch jobs and return normalized records plus raw payloads."""
