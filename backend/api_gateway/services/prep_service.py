from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.job import Job
from models.job_score import JobScore as JobScoreRow
from models.prep_session import PrepSession
from schemas.prep import PrepSessionDetailResponse
from services.application_schema import application_to_schema
from services.prep_generation import (
    generate_prep_structured,
    new_prep_session_id,
    prep_structured_to_storage_dict,
)


class PrepApplicationNotFoundError(LookupError):
    pass


async def fetch_application_job_for_user(
    session: AsyncSession, user_id: str, application_id: str
) -> tuple[Application, Job, JobScoreRow | None]:
    """Public export for prep assist (same lookup as prep generation)."""
    return await _application_job_score(session, user_id, application_id)


async def _application_job_score(
    session: AsyncSession, user_id: str, application_id: str
) -> tuple[Application, Job, JobScoreRow | None]:
    stmt = (
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(Application.id == application_id, Application.user_id == user_id)
    )
    row = (await session.execute(stmt)).one_or_none()
    if row is None:
        raise PrepApplicationNotFoundError(application_id)
    app, job = row
    score_row = (
        await session.execute(
            select(JobScoreRow).where(JobScoreRow.user_id == user_id, JobScoreRow.job_id == job.id)
        )
    ).scalar_one_or_none()
    return app, job, score_row


async def prep_row_to_detail(
    session: AsyncSession,
    user_id: str,
    prep_row: PrepSession,
) -> PrepSessionDetailResponse:
    app, job, score_row = await _application_job_score(session, user_id, prep_row.application_id)
    questions = [str(q) for q in (prep_row.questions or [])] if prep_row.questions else []
    star = list(prep_row.star_stories or []) if prep_row.star_stories else []
    return PrepSessionDetailResponse(
        id=prep_row.id,
        application=application_to_schema(app, job, score_row, approval=None),
        questions=questions,
        star_stories=star,
        company_brief=prep_row.company_brief or "",
        created_at=prep_row.created_at,
    )


async def get_prep_detail_for_user(
    session: AsyncSession, user_id: str, application_id: str
) -> PrepSessionDetailResponse | None:
    stmt = (
        select(PrepSession)
        .join(Application, Application.id == PrepSession.application_id)
        .where(PrepSession.application_id == application_id, Application.user_id == user_id)
        .order_by(PrepSession.created_at.desc())
        .limit(1)
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        return None
    return await prep_row_to_detail(session, user_id, row)


async def generate_prep_for_application(
    session: AsyncSession, user_id: str, application_id: str
) -> PrepSessionDetailResponse:
    app, job, _score_row = await _application_job_score(session, user_id, application_id)

    structured = await generate_prep_structured(job)
    questions, stories, brief = prep_structured_to_storage_dict(structured, job)

    prep_row = PrepSession(
        id=new_prep_session_id(),
        user_id=user_id,
        application_id=app.id,
        questions=questions,
        star_stories=stories,
        company_brief=brief,
    )
    session.add(prep_row)
    await session.commit()
    await session.refresh(prep_row)

    return await prep_row_to_detail(session, user_id, prep_row)
