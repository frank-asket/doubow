"""Import / upsert jobs into the shared catalog (discovery feed → Postgres)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from schemas.jobs import DiscoverJobsRequest, DiscoverJobsResponse
from services.jobs_service import _sync_template_scores_for_user


def _default_score_template() -> dict:
    return {
        "fit_score": 3.5,
        "fit_reasons": ["Imported via discovery — refine after you review the fit"],
        "risk_flags": [],
        "dimension_scores": {
            "tech": 3.5,
            "culture": 3.5,
            "seniority": 3.5,
            "comp": 3.5,
            "location": 3.5,
            "channel_recommendation": "email",
        },
    }


async def discover_upsert_jobs(
    session: AsyncSession, user_id: str, payload: DiscoverJobsRequest
) -> DiscoverJobsResponse:
    """Upsert jobs by (source, external_id); sync template-driven scores for this user."""
    created = 0
    updated = 0
    job_ids: list[str] = []

    for item in payload.jobs:
        stmt = select(Job).where(Job.source == item.source, Job.external_id == item.external_id)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        template = item.score_template if isinstance(item.score_template, dict) else _default_score_template()

        if existing is None:
            row = Job(
                id=str(uuid4()),
                source=item.source,
                external_id=item.external_id,
                title=item.title,
                company=item.company,
                location=item.location,
                salary_range=item.salary_range,
                description=item.description or None,
                url=item.url or None,
                posted_at=item.posted_at,
                discovered_at=datetime.now(timezone.utc),
                score_template=template,
            )
            session.add(row)
            await session.flush()
            job_ids.append(row.id)
            created += 1
        else:
            existing.title = item.title
            existing.company = item.company
            existing.location = item.location
            existing.salary_range = item.salary_range
            existing.description = item.description or None
            existing.url = item.url or None
            if item.posted_at is not None:
                existing.posted_at = item.posted_at
            existing.score_template = template
            await session.flush()
            job_ids.append(existing.id)
            updated += 1

    await session.commit()

    await _sync_template_scores_for_user(session, user_id)

    return DiscoverJobsResponse(created=created, updated=updated, job_ids=job_ids)
