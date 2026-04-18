from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.job import Job
from models.job_score import JobScore as JobScoreRow
from schemas.applications import (
    Application as ApplicationSchema,
    ApplicationsListResponse,
    CreateApplicationRequest,
    IntegrityChange,
    IntegrityCheckResponse,
    IntegritySummary,
)
from schemas.jobs import Job as JobSchema
from services.job_score_mapping import job_score_to_api


def _to_schema(app: Application, job: Job, score_row: JobScoreRow | None) -> ApplicationSchema:
    return ApplicationSchema(
        id=app.id,
        user_id=app.user_id,
        job=JobSchema(
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
        ),
        score=job_score_to_api(job.id, score_row),
        status=app.status,
        channel=app.channel,
        applied_at=app.applied_at,
        last_updated=app.last_updated,
        idempotency_key=app.idempotency_key,
        notes=app.notes,
        is_stale=app.is_stale,
        dedup_group=app.dedup_group,
    )


async def list_applications(session: AsyncSession, user_id: str, status: str | None) -> ApplicationsListResponse:
    stmt = (
        select(Application, Job, JobScoreRow)
        .join(Job, Job.id == Application.job_id)
        .outerjoin(
            JobScoreRow,
            (JobScoreRow.job_id == Job.id) & (JobScoreRow.user_id == Application.user_id),
        )
        .where(Application.user_id == user_id)
    )
    if status:
        stmt = stmt.where(Application.status == status)
    rows = (await session.execute(stmt.order_by(Application.last_updated.desc()))).all()
    items = [_to_schema(app, job, score_row) for app, job, score_row in rows]
    return ApplicationsListResponse(items=items, total=len(items), page=1, per_page=20)


async def create_application(session: AsyncSession, user_id: str, payload: CreateApplicationRequest) -> ApplicationSchema:
    job = await session.get(Job, payload.job_id)
    if not job:
        job = Job(
            id=payload.job_id,
            source="manual",
            external_id=f"seed-{uuid4().hex[:10]}",
            title="Generated role",
            company="Unknown",
            location="Remote",
            description="Seeded from application create",
            url="https://example.com/jobs/generated",
        )
        session.add(job)
        await session.flush()

    app = Application(
        id=f"app_{uuid4().hex[:12]}",
        user_id=user_id,
        job_id=job.id,
        status="pending",
        channel=payload.channel,
        idempotency_key=f"app-{uuid4().hex[:12]}",
    )
    session.add(app)
    await session.commit()
    await session.refresh(app)
    score_row = (
        await session.execute(
            select(JobScoreRow).where(JobScoreRow.user_id == user_id, JobScoreRow.job_id == job.id)
        )
    ).scalar_one_or_none()
    return _to_schema(app, job, score_row)


async def integrity_check(session: AsyncSession, user_id: str, mode: str) -> IntegrityCheckResponse:
    rows = (
        await session.execute(
            select(Application).where(Application.user_id == user_id).order_by(Application.last_updated.desc())
        )
    ).scalars().all()
    stale = [row for row in rows if row.is_stale]
    dupes = [row for row in rows if row.dedup_group]
    changes: list[IntegrityChange] = []

    if dupes:
        ids = [item.id for item in dupes]
        changes.append(
            IntegrityChange(
                type="deduplicate",
                application_ids=ids,
                keep_id=ids[0],
                reason="Duplicate applications share the same dedup group",
            )
        )
    for item in stale:
        changes.append(
            IntegrityChange(
                type="mark_stale",
                application_ids=[item.id],
                reason="No update in the past 30 days.",
            )
        )

    if mode == "apply":
        for item in rows:
            item.is_stale = False
            item.dedup_group = None
        await session.commit()

    return IntegrityCheckResponse(
        mode=mode,
        summary=IntegritySummary(duplicates=len(dupes), stale=len(stale), status_fixes=0),
        changes=changes,
    )
