"""Increment ``users.profile_views`` (recruiter/employer impressions)."""

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def increment_profile_views(session: AsyncSession, user_id: str, delta: int = 1) -> int:
    """Add ``delta`` to the user's profile view count (NULL treated as 0). Returns the new total."""
    if delta < 1:
        raise ValueError("delta must be >= 1")

    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(profile_views=func.coalesce(User.profile_views, 0) + delta)
        .returning(User.profile_views)
    )
    result = await session.execute(stmt)
    new_total = result.scalar_one_or_none()
    await session.commit()
    if new_total is None:
        raise LookupError(f"user not found: {user_id}")
    return int(new_total)
