#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from sqlalchemy import text

from db.session import SessionLocal
from services.greenhouse_adapter import GreenhouseAdapter
from services.job_provider_ingestion_service import ingest_provider_jobs_paginated
from services.jobs_service import list_jobs
from services.provider_adapter import ProviderFetchParams

FIELDS = [
    ("backend", "backend engineer"),
    ("frontend", "frontend engineer"),
    ("data", "data engineer"),
    ("security", "security engineer"),
    ("ai_ml", "machine learning engineer"),
]


async def main() -> None:
    async with SessionLocal() as session:
        user = (await session.execute(text("SELECT id, email FROM users ORDER BY created_at DESC LIMIT 1"))).first()
        if not user:
            print("NO_USERS_FOUND")
            return
        user_id = user.id
        print(f"TEST_USER_ID={user.id} EMAIL={user.email}")

        before = await list_jobs(session, user_id=user_id, min_fit=0.0, location=None, page=1, per_page=300)
        before_greenhouse = sum(1 for j in before.items if j.source == "greenhouse")
        print(f"BEFORE_TOTAL_ITEMS={len(before.items)} BEFORE_GREENHOUSE_ITEMS={before_greenhouse}")

        adapter = GreenhouseAdapter(board_tokens=["vercel"])

        total_created = 0
        total_updated = 0
        total_deduped = 0
        runs: list[tuple[str, str, int, int, int, str]] = []

        for label, keyword in FIELDS:
            summary = await ingest_provider_jobs_paginated(
                session,
                user_id=user_id,
                adapter=adapter,
                base_params=ProviderFetchParams(
                    keywords=keyword,
                    location="remote",
                    country=None,
                    page=1,
                    per_page=10,
                ),
                pages=1,
            )
            created = int(summary.get("created", 0) or 0)
            updated = int(summary.get("updated", 0) or 0)
            deduped = int(summary.get("deduped", 0) or 0)
            run_id = (summary.get("run_ids") or [""])[0]

            total_created += created
            total_updated += updated
            total_deduped += deduped
            runs.append((label, keyword, created, updated, deduped, run_id))

        after = await list_jobs(session, user_id=user_id, min_fit=0.0, location=None, page=1, per_page=300)
        after_greenhouse = sum(1 for j in after.items if j.source == "greenhouse")

        print("FIELD_RESULTS_START")
        for label, keyword, created, updated, deduped, run_id in runs:
            print(
                f"FIELD={label} KEYWORD={keyword} CREATED={created} "
                f"UPDATED={updated} DEDUPED={deduped} RUN_ID={run_id}"
            )
        print("FIELD_RESULTS_END")

        print(f"TOTAL_CREATED={total_created} TOTAL_UPDATED={total_updated} TOTAL_DEDUPED={total_deduped}")
        print(f"AFTER_TOTAL_ITEMS={len(after.items)} AFTER_GREENHOUSE_ITEMS={after_greenhouse}")


if __name__ == "__main__":
    asyncio.run(main())
