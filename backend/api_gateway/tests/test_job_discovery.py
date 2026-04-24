"""Job discovery upsert creates scores via template sync."""

import pytest

from models.user import User
from schemas.jobs import DiscoverJobItem, DiscoverJobsRequest
from services.job_discovery_service import discover_upsert_jobs
from services.jobs_service import list_jobs


@pytest.mark.asyncio
async def test_discover_creates_job_and_visible_in_list(db_session):
    uid = "user_disc_1"
    db_session.add(User(id=uid, email="disc@example.com"))
    await db_session.commit()

    req = DiscoverJobsRequest(
        jobs=[
            DiscoverJobItem(
                source="manual",
                external_id="disc-001",
                title="Platform Engineer",
                company="TestCorp",
                location="Remote",
                description="Build systems",
                url="https://example.com/careers/1",
            )
        ]
    )

    out = await discover_upsert_jobs(db_session, uid, req)
    assert out.created == 1
    assert out.updated == 0

    listing = await list_jobs(db_session, uid, min_fit=0.0, location=None, page=1)
    assert listing.total >= 1
    match = next((j for j in listing.items if j.company == "TestCorp"), None)
    assert match is not None
    assert match.logo_url is not None and match.logo_url.startswith("https://")
    assert match.description_raw == "Build systems"
    assert match.description_clean == "Build systems"
    assert match.canonical_url.startswith("https://")
