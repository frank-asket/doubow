from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from schemas.jobs import DimensionScores, JobScore, JobsListResponse, JobWithScore


def _job_to_schema(job: Job) -> JobWithScore:
    now = datetime.now(timezone.utc)
    return JobWithScore(
        id=job.id,
        source=job.source,
        external_id=job.external_id,
        title=job.title,
        company=job.company,
        location=job.location or "Remote",
        salary_range=job.salary_range,
        description=job.description or "",
        url=job.url or "",
        posted_at=job.posted_at,
        discovered_at=job.discovered_at,
        score=JobScore(
            job_id=job.id,
            fit_score=4.2,
            fit_reasons=["Profile and role share relevant stack"],
            risk_flags=[],
            dimension_scores=DimensionScores(tech=4.2, culture=4.0, seniority=4.3, comp=4.1, location=4.4),
            channel_recommendation="email",
            scored_at=now,
        ),
    )


async def list_jobs(
    session: AsyncSession,
    min_fit: float,
    location: str | None,
    page: int,
    per_page: int = 20,
) -> JobsListResponse:
    stmt: Select[tuple[Job]] = select(Job).order_by(Job.discovered_at.desc())
    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location.strip()}%"))

    jobs = (await session.execute(stmt.offset((page - 1) * per_page).limit(per_page))).scalars().all()

    if not jobs:
        seed = Job(
            id=str(uuid4()),
            source="manual",
            external_id=f"seed-{uuid4().hex[:10]}",
            title="Senior ML Engineer",
            company="Mistral AI",
            location="Remote · Paris",
            salary_range="EUR130k-EUR160k",
            description="Build production RAG and agentic systems.",
            url="https://example.com/jobs/senior-ml-engineer",
        )
        session.add(seed)
        await session.commit()
        await session.refresh(seed)
        jobs = [seed]

    items = [_job_to_schema(job) for job in jobs]
    items = [item for item in items if item.score.fit_score >= min_fit]
    return JobsListResponse(items=items, total=len(items), page=page, per_page=per_page)
