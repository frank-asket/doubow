from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.resume import ResumeResponse
from services.resume_service import get_resume_for_user

router = APIRouter(prefix="/me", tags=["resume"])


@router.get("/resume", response_model=ResumeResponse)
async def get_resume(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ResumeResponse:
    res = await get_resume_for_user(session, user.id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return res
