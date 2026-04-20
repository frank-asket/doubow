from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.jobs import JobsListResponse
from services.jobs_service import dismiss_job_for_user, list_jobs as list_jobs_service

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


@router.post("/{job_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> None:
    try:
        await dismiss_job_for_user(session=session, user_id=user.id, job_id=job_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from None
