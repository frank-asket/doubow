#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from sqlalchemy import text

from db.session import SessionLocal
from services.greenhouse_adapter import GreenhouseAdapter
from services.job_provider_ingestion_service import ingest_provider_jobs_paginated
from services.jobs_service import list_jobs
from services.provider_adapter import ProviderFetchParams


async def main() -> None:
    async with SessionLocal() as session:
        user = (await session.execute(text("SELECT id, email FROM users ORDER BY created_at DESC LIMIT 1"))).first()
        if not user:
            print("NO_USERS_FOUND")
            return
        user_id = user.id
        print(f"USER_ID={user.id} EMAIL={user.email}")

        before = await list_jobs(session, user_id=user_id, min_fit=0.0, location=None, page=1, per_page=200)
        before_greenhouse = sum(1 for j in before.items if j.source == "greenhouse")
        print(f"BEFORE_TOTAL_ITEMS={len(before.items)} BEFORE_GREENHOUSE_ITEMS={before_greenhouse}")

        adapter = GreenhouseAdapter(board_tokens=["vercel"])
        summary = await ingest_provider_jobs_paginated(
            session,
            user_id=user_id,
            adapter=adapter,
            base_params=ProviderFetchParams(
                keywords="engineer",
                location=None,
                country=None,
                page=1,
                per_page=20,
            ),
            pages=1,
        )
        print(f"INGEST_SUMMARY={summary}")

        after = await list_jobs(session, user_id=user_id, min_fit=0.0, location=None, page=1, per_page=200)
        after_greenhouse = sum(1 for j in after.items if j.source == "greenhouse")
        print(f"AFTER_TOTAL_ITEMS={len(after.items)} AFTER_GREENHOUSE_ITEMS={after_greenhouse}")

        db_count = (await session.execute(text("SELECT COUNT(*) FROM jobs WHERE source='greenhouse'"))).scalar_one()
        print(f"DB_GREENHOUSE_TOTAL={db_count}")


if __name__ == "__main__":
    asyncio.run(main())
