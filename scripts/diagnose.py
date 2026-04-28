#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "backend" / "api_gateway"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from db.session import SessionLocal  # noqa: E402
from ingestion.scheduler.ingestion_engine import ALL_CONNECTORS, run_ingestion  # noqa: E402
from sqlalchemy import text  # noqa: E402


async def run_diagnostics(source: str | None, fix: bool) -> dict:
    selected = [source] if source else list(ALL_CONNECTORS.keys())
    health: dict[str, dict] = {}
    for name in selected:
        connector_cls = ALL_CONNECTORS[name]
        health[name] = await connector_cls().health_check()

    async with SessionLocal() as session:
        total = (
            await session.execute(text("SELECT COUNT(*) FROM jobs WHERE coalesce(is_active, true) = true"))
        ).scalar()
        by_source_rows = (
            await session.execute(
                text(
                    """
                    SELECT source, COUNT(*) AS cnt, MAX(discovered_at) AS last_seen
                    FROM jobs
                    WHERE coalesce(is_active, true) = true
                    GROUP BY source
                    ORDER BY cnt DESC
                    """
                )
            )
        ).fetchall()
        by_source = [
            {"source": row[0], "count": row[1], "last_seen": row[2].isoformat() if row[2] else None}
            for row in by_source_rows
        ]

        fix_summary = None
        if fix:
            fix_summary = (await run_ingestion(session, selected if source else None)).to_dict()

    return {"total_active_jobs": total or 0, "by_source": by_source, "health": health, "fix_result": fix_summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose and optionally trigger ingestion.")
    parser.add_argument("--source", type=str, default=None, help="single source name")
    parser.add_argument("--fix", action="store_true", help="trigger ingestion run now")
    parser.add_argument("--json", action="store_true", help="output raw JSON")
    args = parser.parse_args()
    report = asyncio.run(run_diagnostics(source=args.source, fix=args.fix))
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"total_active_jobs={report['total_active_jobs']}")
    for row in report["by_source"]:
        print(f"{row['source']}\t{row['count']}\t{row['last_seen']}")
    for source, status in report["health"].items():
        print(f"health[{source}]={status.get('status')}")
    if report["fix_result"]:
        print(
            "fix_result:"
            f" fetched={report['fix_result']['total_fetched']}"
            f" inserted={report['fix_result']['total_inserted']}"
            f" errors={report['fix_result']['total_errors']}"
        )


if __name__ == "__main__":
    main()

