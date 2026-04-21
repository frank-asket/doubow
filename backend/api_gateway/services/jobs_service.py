from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from models.job_dismissal import JobDismissal
from models.job_score import JobScore
from schemas.jobs import JobsListResponse, JobWithScore
from services.job_score_mapping import job_score_to_api


def _row_to_schema(job: Job, score_row: JobScore) -> JobWithScore:
    score = job_score_to_api(job.id, score_row)
    assert score is not None
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
        score=score,
    )


def _score_spec_from_template(raw: dict | None) -> dict | None:
    if not isinstance(raw, dict):
        return None
    required = ("fit_score", "fit_reasons", "risk_flags", "dimension_scores")
    if not all(k in raw for k in required):
        return None
    return raw


async def _sync_template_scores_for_user(session: AsyncSession, user_id: str) -> None:
    """Create job_scores from jobs.score_template when the user has neither a score nor a dismissal."""
    stmt = select(Job).where(Job.score_template.isnot(None))
    jobs_with_templates = (await session.execute(stmt)).scalars().all()
    if not jobs_with_templates:
        return

    catalog_ids = [j.id for j in jobs_with_templates]
    scored_rows = (
        await session.execute(select(JobScore.job_id).where(JobScore.user_id == user_id, JobScore.job_id.in_(catalog_ids)))
    ).all()
    scored = {r[0] for r in scored_rows}

    dismissed_rows = (
        await session.execute(
            select(JobDismissal.job_id).where(JobDismissal.user_id == user_id, JobDismissal.job_id.in_(catalog_ids))
        )
    ).all()
    dismissed = {r[0] for r in dismissed_rows}

    now = datetime.now(timezone.utc)
    for job in jobs_with_templates:
        if job.id in scored or job.id in dismissed:
            continue
        spec = _score_spec_from_template(job.score_template if isinstance(job.score_template, dict) else None)
        if spec is None:
            continue
        session.add(
            JobScore(
                id=str(uuid4()),
                user_id=user_id,
                job_id=job.id,
                fit_score=spec["fit_score"],
                fit_reasons=spec["fit_reasons"],
                risk_flags=spec["risk_flags"],
                dimension_scores=spec["dimension_scores"],
                scored_at=now,
            )
        )
    await session.commit()


async def list_jobs(
    session: AsyncSession,
    user_id: str,
    min_fit: float,
    location: str | None,
    page: int,
    per_page: int = 20,
) -> JobsListResponse:
    await _sync_template_scores_for_user(session, user_id)

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


async def dismiss_job_for_user(session: AsyncSession, user_id: str, job_id: str) -> None:
    job = await session.get(Job, job_id)
    if job is None:
        raise LookupError("job_not_found")

    await session.execute(delete(JobScore).where(JobScore.user_id == user_id, JobScore.job_id == job_id))

    existing = (
        await session.execute(
            select(JobDismissal).where(JobDismissal.user_id == user_id, JobDismissal.job_id == job_id)
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(JobDismissal(user_id=user_id, job_id=job_id))

    await session.commit()
