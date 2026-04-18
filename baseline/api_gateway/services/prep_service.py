from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.prep_session import PrepSession
from schemas.prep import PrepSessionResponse


async def get_prep_for_user(session: AsyncSession, user_id: str, application_id: str) -> PrepSessionResponse | None:
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
    questions = [str(q) for q in (row.questions or [])] if row.questions else []
    star = list(row.star_stories or []) if row.star_stories else []
    return PrepSessionResponse(
        id=row.id,
        questions=questions,
        star_stories=star,
        company_brief=row.company_brief or "",
    )
