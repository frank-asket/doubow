#!/usr/bin/env python3
"""Lightweight Adzuna ingestion scheduler (once/hourly/daily) with pagination.

Examples:
  python backend/scripts/adzuna_ingestion_runner.py --mode once --pages 3 --keywords "software engineer"
  python backend/scripts/adzuna_ingestion_runner.py --mode hourly --pages 2 --location "Berlin"
  python backend/scripts/adzuna_ingestion_runner.py --mode daily --country us --per-page 50
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import logging
import sys
from pathlib import Path

# Allow local imports when run from repo root.
_API = Path(__file__).resolve().parent.parent / "api_gateway"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from config import settings  # noqa: E402
from db.dotenv_merge import load_dotenv_merged  # noqa: E402
from db.session import SessionLocal  # noqa: E402
from services.adzuna_adapter import AdzunaAdapter  # noqa: E402
from services.job_provider_ingestion_service import ingest_provider_jobs_paginated  # noqa: E402
from services.provider_adapter import ProviderFetchParams  # noqa: E402

logger = logging.getLogger("adzuna_ingestion_runner")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run paginated Adzuna ingestion in once/hourly/daily modes.")
    parser.add_argument("--mode", choices=["once", "hourly", "daily"], default="once")
    parser.add_argument("--country", default=None)
    parser.add_argument("--keywords", default=None)
    parser.add_argument("--location", default=None)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument(
        "--user-id",
        default=None,
        help="Catalog ingestion actor id. Defaults to JOB_CATALOG_INGESTION_USER_ID.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=None,
        help="Override schedule interval (defaults: hourly=3600, daily=86400).",
    )
    return parser.parse_args()


def _default_interval_seconds(mode: str) -> int:
    if mode == "hourly":
        return 3600
    if mode == "daily":
        return 86400
    return 0


async def _run_once(args: argparse.Namespace) -> None:
    actor_user_id = (args.user_id or settings.job_catalog_ingestion_user_id).strip()
    if not actor_user_id:
        raise RuntimeError("Missing ingestion actor user id (set JOB_CATALOG_INGESTION_USER_ID or pass --user-id)")

    adapter = AdzunaAdapter(default_country=args.country)
    params = ProviderFetchParams(
        keywords=args.keywords,
        location=args.location,
        country=args.country,
        page=max(1, args.start_page),
        per_page=max(1, min(50, args.per_page)),
    )
    async with SessionLocal() as session:
        summary = await ingest_provider_jobs_paginated(
            session,
            user_id=actor_user_id,
            adapter=adapter,
            base_params=params,
            pages=max(1, args.pages),
        )
    logger.info(
        "adzuna ingestion complete mode=%s pages=%s created=%s updated=%s runs=%s",
        args.mode,
        summary["pages"],
        summary["created"],
        summary["updated"],
        len(summary["run_ids"]),
    )


async def _main() -> None:
    load_dotenv_merged(_API / "db" / "migrations")
    args = _parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if args.mode == "once":
        await _run_once(args)
        return

    interval = args.interval_seconds or _default_interval_seconds(args.mode)
    while True:
        started = datetime.now(timezone.utc)
        try:
            await _run_once(args)
        except Exception:
            logger.exception("adzuna ingestion cycle failed mode=%s started_at=%s", args.mode, started.isoformat())
        await asyncio.sleep(max(30, interval))


if __name__ == "__main__":
    asyncio.run(_main())
