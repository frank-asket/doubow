from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.jobs import JobsListResponse
from services.jobs_service import list_jobs as list_jobs_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobsListResponse)
async def list_jobs(
    min_fit: float = Query(default=0.0, ge=0.0, le=5.0),
    location: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> JobsListResponse:
    return await list_jobs_service(
        session=session, user_id=user.id, min_fit=min_fit, location=location, page=page
    )
