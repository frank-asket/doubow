from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from sqlalchemy import text


@dataclass
class RawJob:
    source: str
    external_id: str
    title: str
    company: str
    url: str
    description: str
    location: str = ""
    remote: bool = False
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str = "USD"
    posted_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    department: str = ""
    employment_type: str = "full_time"
    extra: dict = field(default_factory=dict)


@dataclass
class JobRecord:
    source: str
    external_id: str
    dedup_hash: str
    title: str
    company: str
    url: str
    description: str
    location: str
    remote: bool
    salary_range: str
    salary_min: int | None
    salary_max: int | None
    currency: str
    posted_at: datetime | None
    discovered_at: datetime
    tags: list[str]
    department: str
    employment_type: str
    is_active: bool = True
    raw_json: dict = field(default_factory=dict)

    def to_db_dict(self) -> dict:
        payload = asdict(self)
        # Keep JSON and datetime values as native Python objects so asyncpg can
        # bind them to JSONB / TIMESTAMPTZ columns without type coercion errors.
        return payload


@dataclass
class ConnectorResult:
    source: str
    run_id: str
    success: bool
    fetched: int = 0
    inserted: int = 0
    skipped_dupe: int = 0
    skipped_filter: int = 0
    errors: int = 0
    duration_s: float = 0.0
    error_detail: str = ""


class BaseConnector(ABC):
    source_name: str = "unknown"
    rate_limit_rps: float = 2.0
    max_retries: int = 3
    timeout_s: float = 30.0

    def __init__(self) -> None:
        self._run_id = str(uuid.uuid4())
        self._client: httpx.AsyncClient | None = None
        self._last_req = 0.0

    async def run(self, db_session, existing_hashes: set[str]) -> ConnectorResult:
        result = ConnectorResult(source=self.source_name, run_id=self._run_id, success=False)
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                self._client = client
                async for raw in self.fetch():
                    result.fetched += 1
                    record = self._normalise(raw)
                    if record.dedup_hash in existing_hashes:
                        result.skipped_dupe += 1
                        continue
                    if not self._passes_quality_filter(record):
                        result.skipped_filter += 1
                        continue
                    try:
                        await self._upsert(db_session, record)
                        existing_hashes.add(record.dedup_hash)
                        result.inserted += 1
                    except Exception:
                        result.errors += 1
            result.success = True
        except Exception as exc:
            result.error_detail = str(exc)
        finally:
            result.duration_s = round(time.perf_counter() - start, 2)
        return result

    @abstractmethod
    async def fetch(self) -> AsyncIterator[RawJob]:
        ...

    async def health_check(self) -> dict:
        try:
            count = 0
            async with httpx.AsyncClient(timeout=8.0) as client:
                self._client = client
                async for _ in self.fetch():
                    count += 1
                    if count >= 3:
                        break
            return {"status": "ok", "source": self.source_name, "sample_count": count}
        except Exception as exc:
            return {"status": "error", "source": self.source_name, "error": str(exc)}

    async def _rate_limit(self) -> None:
        if self.rate_limit_rps <= 0:
            return
        min_interval = 1.0 / self.rate_limit_rps
        elapsed = time.perf_counter() - self._last_req
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_req = time.perf_counter()

    async def _get(self, url: str, **kwargs) -> httpx.Response:
        if self._client is None:
            raise RuntimeError("HTTP client not initialized")
        await self._rate_limit()
        for attempt in range(self.max_retries):
            try:
                response = await self._client.get(url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {429, 503} and attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise
            except (httpx.ConnectError, httpx.ReadTimeout):
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise

    def _normalise(self, raw: RawJob) -> JobRecord:
        dedup_hash = hashlib.sha256(f"{raw.source}:{raw.external_id}".encode()).hexdigest()[:32]
        return JobRecord(
            source=raw.source,
            external_id=str(raw.external_id),
            dedup_hash=dedup_hash,
            title=raw.title.strip(),
            company=raw.company.strip(),
            url=raw.url,
            description=(raw.description or "")[:8000],
            location=raw.location or ("Remote" if raw.remote else ""),
            remote=raw.remote,
            salary_range=self._format_salary(raw.salary_min, raw.salary_max, raw.currency),
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            currency=raw.currency,
            posted_at=raw.posted_at,
            discovered_at=datetime.now(timezone.utc),
            tags=raw.tags[:20],
            department=raw.department,
            employment_type=raw.employment_type,
            raw_json={"source": raw.source, "external_id": raw.external_id, "extra": raw.extra},
        )

    @staticmethod
    def _format_salary(min_val: int | None, max_val: int | None, currency: str) -> str:
        symbols = {"USD": "$", "EUR": "EUR ", "GBP": "GBP "}
        symbol = symbols.get(currency, f"{currency} ")
        if min_val and max_val:
            return f"{symbol}{min_val}-{symbol}{max_val}"
        if min_val:
            return f"{symbol}{min_val}+"
        if max_val:
            return f"up to {symbol}{max_val}"
        return ""

    @staticmethod
    def _passes_quality_filter(record: JobRecord) -> bool:
        return bool(
            record.title
            and record.company
            and record.url.startswith("http")
            and len(record.description) >= 40
        )

    @staticmethod
    async def _upsert(db_session, record: JobRecord) -> None:
        sql = text(
            """
            INSERT INTO jobs (
                source, external_id, dedup_hash, title, company, url,
                description, location, remote, salary_range, salary_min,
                salary_max, currency, posted_at, discovered_at, tags,
                department, employment_type, is_active, raw_json
            ) VALUES (
                :source, :external_id, :dedup_hash, :title, :company, :url,
                :description, :location, :remote, :salary_range, :salary_min,
                :salary_max, :currency, :posted_at, :discovered_at, :tags,
                :department, :employment_type, :is_active, :raw_json
            )
            ON CONFLICT (source, external_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                salary_range = EXCLUDED.salary_range,
                salary_min = EXCLUDED.salary_min,
                salary_max = EXCLUDED.salary_max,
                posted_at = EXCLUDED.posted_at,
                discovered_at = EXCLUDED.discovered_at,
                is_active = true
            """
        )
        await db_session.execute(sql, record.to_db_dict())

