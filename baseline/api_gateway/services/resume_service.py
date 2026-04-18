from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume
from schemas.resume import ResumeResponse


async def get_resume_for_user(session: AsyncSession, user_id: str) -> ResumeResponse | None:
    stmt = (
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc(), Resume.version.desc())
        .limit(1)
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        return None
    return ResumeResponse(
        id=row.id,
        storage_path=row.storage_path,
        parsed_profile=row.parsed_profile or {},
        preferences=row.preferences or {},
        version=row.version,
    )
