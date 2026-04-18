from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from models.job_score import JobScore
from schemas.jobs import Channel, DimensionScores, JobScore as JobScoreSchema, JobsListResponse, JobWithScore


def _dimension_scores(raw: dict) -> DimensionScores:
    return DimensionScores(
        tech=float(raw.get("tech", 3.0)),
        culture=float(raw.get("culture", 3.0)),
        seniority=float(raw.get("seniority", 3.0)),
        comp=float(raw.get("comp", 3.0)),
        location=float(raw.get("location", 3.0)),
    )


def _channel(raw: dict) -> Channel:
    ch = raw.get("channel_recommendation", "email")
    if ch in ("email", "linkedin", "company_site"):
        return ch  # type: ignore[return-value]
    return "email"


def _row_to_schema(job: Job, score_row: JobScore) -> JobWithScore:
    dims_raw = score_row.dimension_scores if isinstance(score_row.dimension_scores, dict) else {}
    return JobWithScore(
        id=job.id,
        source=job.source,  # type: ignore[arg-type]
        external_id=job.external_id,
        title=job.title,
        company=job.company,
        location=job.location or "Remote",
        salary_range=job.salary_range,
        description=job.description or "",
        url=job.url or "",
        posted_at=job.posted_at,
        discovered_at=job.discovered_at,
        score=JobScoreSchema(
            job_id=job.id,
            fit_score=float(score_row.fit_score),
            fit_reasons=list(score_row.fit_reasons or []),
            risk_flags=list(score_row.risk_flags or []),
            dimension_scores=_dimension_scores(dims_raw),
            channel_recommendation=_channel(dims_raw),
            scored_at=score_row.scored_at,
        ),
    )


async def _seed_user_demo_job(session: AsyncSession, user_id: str) -> None:
    now = datetime.now(timezone.utc)
    job = Job(
        id=str(uuid4()),
        source="manual",
        external_id=f"seed-{uuid4().hex[:10]}",
        title="Senior ML Engineer",
        company="Mistral AI",
        location="Remote · Paris",
        salary_range="EUR130k-EUR160k",
        description="Build production RAG and agentic systems.",
        url="https://example.com/jobs/senior-ml-engineer",
        posted_at=now,
    )
    dims = {"tech": 4.2, "culture": 4.0, "seniority": 4.3, "comp": 4.1, "location": 4.4, "channel_recommendation": "email"}
    score_row = JobScore(
        id=str(uuid4()),
        user_id=user_id,
        job_id=job.id,
        fit_score=4.2,
        fit_reasons=["Profile and role share relevant stack"],
        risk_flags=[],
        dimension_scores=dims,
        scored_at=now,
    )
    session.add(job)
    session.add(score_row)
    await session.commit()


async def list_jobs(
    session: AsyncSession,
    user_id: str,
    min_fit: float,
    location: str | None,
    page: int,
    per_page: int = 20,
) -> JobsListResponse:
    any_for_user = (
        await session.execute(select(func.count(JobScore.id)).where(JobScore.user_id == user_id))
    ).scalar_one()
    if any_for_user == 0 and page == 1:
        await _seed_user_demo_job(session, user_id)

    filters = [JobScore.user_id == user_id, JobScore.fit_score >= min_fit]
    if location:
        filters.append(Job.location.ilike(f"%{location.strip()}%"))

    count_stmt = (
        select(func.count())
        .select_from(Job)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(*filters)
    )
    total = (await session.execute(count_stmt)).scalar_one()

    list_stmt = (
        select(Job, JobScore)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(*filters)
        .order_by(JobScore.scored_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    rows = (await session.execute(list_stmt)).all()
    items = [_row_to_schema(job, score_row) for job, score_row in rows]

    return JobsListResponse(items=items, total=int(total), page=page, per_page=per_page)
