#!/usr/bin/env python3
"""Lightweight Greenhouse board ingestion (once / hourly / daily) with pagination.

Requires GREENHOUSE_BOARD_TOKENS (or --boards) and JOB_CATALOG_INGESTION_USER_ID.

Examples:
  python backend/scripts/greenhouse_ingestion_runner.py --mode once --pages 2
  python backend/scripts/greenhouse_ingestion_runner.py --mode hourly --pages 2 --keywords "engineer"
  python backend/scripts/greenhouse_ingestion_runner.py --mode daily --boards "notion,openai"
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import logging
import sys
from pathlib import Path

_API = Path(__file__).resolve().parent.parent / "api_gateway"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from config import settings  # noqa: E402
from db.dotenv_merge import load_dotenv_merged  # noqa: E402
from db.session import SessionLocal  # noqa: E402
from services.greenhouse_adapter import GreenhouseAdapter  # noqa: E402
from services.job_provider_ingestion_service import ingest_provider_jobs_paginated  # noqa: E402
from services.provider_adapter import ProviderFetchParams  # noqa: E402

logger = logging.getLogger("greenhouse_ingestion_runner")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run paginated Greenhouse ingestion in once/hourly/daily modes.")
    parser.add_argument("--mode", choices=["once", "hourly", "daily"], default="once")
    parser.add_argument("--keywords", default=None)
    parser.add_argument("--location", default=None)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument(
        "--boards",
        default=None,
        help="Comma-separated board tokens (overrides GREENHOUSE_BOARD_TOKENS).",
    )
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


def _board_tokens(args: argparse.Namespace) -> list[str]:
    raw = (args.boards or settings.greenhouse_board_tokens or "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


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

    tokens = _board_tokens(args)
    if not tokens:
        raise RuntimeError(
            "No Greenhouse board tokens (set GREENHOUSE_BOARD_TOKENS or pass --boards=slug1,slug2)"
        )

    adapter = GreenhouseAdapter(board_tokens=tokens)
    params = ProviderFetchParams(
        keywords=args.keywords,
        location=args.location,
        country=None,
        page=max(1, args.start_page),
        per_page=max(1, min(100, args.per_page)),
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
        "greenhouse ingestion complete mode=%s pages=%s created=%s updated=%s deduped=%s runs=%s",
        args.mode,
        summary["pages"],
        summary["created"],
        summary["updated"],
        summary.get("deduped", 0),
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
            logger.exception(
                "greenhouse ingestion cycle failed mode=%s started_at=%s", args.mode, started.isoformat()
            )
        await asyncio.sleep(max(30, interval))


if __name__ == "__main__":
    asyncio.run(_main())
