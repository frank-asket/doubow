from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import text

from services.provider_adapter import ProviderFetchParams

from ingestion.connectors import (
    AshbyConnector,
    GreenhouseConnector,
    LeverConnector,
    LinkedInConnector,
    RemotiveConnector,
    WellfoundConnector,
    YCombinatorConnector,
)
from ingestion.connectors.base import ConnectorResult

ALL_CONNECTORS = {
    "greenhouse": GreenhouseConnector,
    "ashby": AshbyConnector,
    "lever": LeverConnector,
    "remotive": RemotiveConnector,
    "ycombinator": YCombinatorConnector,
    "wellfound": WellfoundConnector,
    "linkedin": LinkedInConnector,
}


def get_active_connectors() -> list[str]:
    raw = os.getenv("DOUBOW_ACTIVE_CONNECTORS", "").strip()
    if not raw:
        return list(ALL_CONNECTORS.keys())
    return [n.strip() for n in raw.split(",") if n.strip() in ALL_CONNECTORS]


@dataclass
class IngestionSummary:
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_s: float = 0.0
    total_fetched: int = 0
    total_inserted: int = 0
    total_dupes: int = 0
    total_errors: int = 0
    results: list[ConnectorResult] = field(default_factory=list)

    def add(self, result: ConnectorResult) -> None:
        self.results.append(result)
        self.total_fetched += result.fetched
        self.total_inserted += result.inserted
        self.total_dupes += result.skipped_dupe
        self.total_errors += result.errors

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_s": self.duration_s,
            "total_fetched": self.total_fetched,
            "total_inserted": self.total_inserted,
            "total_dupes": self.total_dupes,
            "total_errors": self.total_errors,
            "by_source": [
                {
                    "source": r.source,
                    "success": r.success,
                    "fetched": r.fetched,
                    "inserted": r.inserted,
                    "dupes": r.skipped_dupe,
                    "errors": r.errors,
                    "duration_s": r.duration_s,
                    "error": r.error_detail or None,
                }
                for r in self.results
            ],
        }


async def run_ingestion(
    db_session,
    connector_names: list[str] | None = None,
    *,
    fetch_context: ProviderFetchParams | None = None,
) -> IngestionSummary:
    started = datetime.now(timezone.utc)
    summary = IngestionSummary(run_id=str(uuid.uuid4()), started_at=started)
    t0 = time.perf_counter()
    existing_hashes = await _load_existing_hashes(db_session)
    names = connector_names or get_active_connectors()

    tasks = []
    for name in names:
        connector_cls = ALL_CONNECTORS.get(name)
        if connector_cls is None:
            continue
        connector = connector_cls()
        connector.set_fetch_context(fetch_context)
        tasks.append(_run_connector_safe(connector, db_session, existing_hashes))

    for result in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(result, ConnectorResult):
            summary.add(result)
        elif isinstance(result, Exception):
            summary.total_errors += 1

    await db_session.commit()
    summary.completed_at = datetime.now(timezone.utc)
    summary.duration_s = round(time.perf_counter() - t0, 2)
    await _record_run(db_session, summary)
    return summary


async def _run_connector_safe(connector, db_session, existing_hashes: set[str]) -> ConnectorResult:
    try:
        return await connector.run(db_session, existing_hashes)
    except Exception as exc:
        return ConnectorResult(
            source=connector.source_name,
            run_id=getattr(connector, "_run_id", "unknown"),
            success=False,
            errors=1,
            error_detail=str(exc),
        )


async def _load_existing_hashes(db_session) -> set[str]:
    try:
        result = await db_session.execute(text("SELECT dedup_hash FROM jobs WHERE dedup_hash IS NOT NULL"))
        return {row[0] for row in result.fetchall() if row[0]}
    except Exception:
        return set()


async def _record_run(db_session, summary: IngestionSummary) -> None:
    await db_session.execute(
        text(
            """
            INSERT INTO ingestion_runs (
                run_id, started_at, completed_at, total_fetched,
                total_inserted, total_dupes, total_errors, results_json
            ) VALUES (
                :run_id, :started_at, :completed_at, :total_fetched,
                :total_inserted, :total_dupes, :total_errors, :results_json
            )
            """
        ),
        {
            "run_id": summary.run_id,
            "started_at": summary.started_at,
            "completed_at": summary.completed_at,
            "total_fetched": summary.total_fetched,
            "total_inserted": summary.total_inserted,
            "total_dupes": summary.total_dupes,
            "total_errors": summary.total_errors,
            "results_json": __import__("json").dumps(summary.to_dict()["by_source"]),
        },
    )
    await db_session.commit()

