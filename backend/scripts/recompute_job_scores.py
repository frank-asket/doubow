#!/usr/bin/env python3
"""One-shot score refresh for template-backed jobs after resume updates.

Examples:
  python backend/scripts/recompute_job_scores.py --user-id clerk_user_123
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

_API = Path(__file__).resolve().parent.parent / "api_gateway"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from db.dotenv_merge import load_dotenv_merged  # noqa: E402
from db.session import SessionLocal  # noqa: E402
from services.jobs_service import recompute_job_scores_for_user  # noqa: E402


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Force-refresh job scores for one user.")
    parser.add_argument("--user-id", required=True, help="Target user id to refresh.")
    return parser.parse_args()


async def _main() -> None:
    load_dotenv_merged(_API / "db" / "migrations")
    args = _args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    async with SessionLocal() as session:
        refreshed = await recompute_job_scores_for_user(session, args.user_id.strip())
    logging.info("recompute complete user_id=%s refreshed_scores=%s", args.user_id.strip(), refreshed)


if __name__ == "__main__":
    asyncio.run(_main())
