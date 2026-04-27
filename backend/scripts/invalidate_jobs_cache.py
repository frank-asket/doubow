#!/usr/bin/env python3
"""Invalidate jobs:list:* Redis cache keys safely.

Default behavior is dry-run (no deletions) so launch ops can preview impact.

Examples:
  # Preview all jobs list keys
  python backend/scripts/invalidate_jobs_cache.py

  # Delete all jobs list keys
  python backend/scripts/invalidate_jobs_cache.py --execute

  # Preview keys for one user
  python backend/scripts/invalidate_jobs_cache.py --user-id user_123
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Allow local imports when run from repo root.
_API = Path(__file__).resolve().parent.parent / "api_gateway"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from db.dotenv_merge import load_dotenv_merged  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely invalidate jobs list cache keys in Redis.")
    parser.add_argument(
        "--pattern",
        default="jobs:list:*",
        help="Redis SCAN pattern (default: jobs:list:*).",
    )
    parser.add_argument(
        "--user-id",
        action="append",
        default=[],
        help="Optional user id filter. May be provided multiple times.",
    )
    parser.add_argument(
        "--max-keys",
        type=int,
        default=5000,
        help="Safety cap: maximum keys to touch in one run (default: 5000).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete keys. Without this flag the script runs in dry-run mode.",
    )
    return parser.parse_args()


def _redis_url() -> str:
    val = (os.getenv("REDIS_URL") or "").strip()
    if not val:
        raise RuntimeError("REDIS_URL is required.")
    return val


def _matches_user_filters(key: str, user_ids: set[str]) -> bool:
    if not user_ids:
        return True
    # Current key shape: jobs:list:vN:{user_id}:{min_fit}:{location}:{page}:{per_page}
    # Keep this lenient so it still works if we change version segments.
    parts = key.split(":")
    if len(parts) < 4:
        return False
    for uid in user_ids:
        if f":{uid}:" in key:
            return True
    return False


async def _main() -> int:
    load_dotenv_merged(_API / "db" / "migrations")
    args = _parse_args()
    user_ids = {u.strip() for u in args.user_id if u and u.strip()}

    try:
        from redis.asyncio import Redis
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: redis dependency unavailable: {exc}")
        return 2

    redis_url = _redis_url()
    client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    try:
        try:
            matched: list[str] = []
            async for key in client.scan_iter(match=args.pattern):
                if not _matches_user_filters(key, user_ids):
                    continue
                matched.append(key)
                if len(matched) >= max(1, args.max_keys):
                    break
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: redis scan failed: {exc}")
            print("Hint: run this via Railway for production internal Redis access.")
            return 2

        mode = "EXECUTE" if args.execute else "DRY-RUN"
        print(f"MODE={mode}")
        print(f"PATTERN={args.pattern}")
        print(f"USER_FILTERS={','.join(sorted(user_ids)) if user_ids else '(none)'}")
        print(f"MATCHED_KEYS={len(matched)}")
        if matched:
            sample = matched[:20]
            print("SAMPLE_KEYS_START")
            for key in sample:
                print(key)
            print("SAMPLE_KEYS_END")

        if len(matched) >= max(1, args.max_keys):
            print(f"WARNING: reached --max-keys cap ({args.max_keys}). Narrow filters or increase cap.")

        if args.execute and matched:
            try:
                deleted = await client.delete(*matched)
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR: redis delete failed: {exc}")
                return 2
            print(f"DELETED_KEYS={deleted}")
        elif args.execute:
            print("DELETED_KEYS=0")

        return 0
    finally:
        await client.aclose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
