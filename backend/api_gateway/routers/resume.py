from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.resume import OnboardingStatusResponse, ResumeAnalyzeResponse, ResumeProfileResponse
from services.resume_service import (
    analyze_resume_for_user,
    get_onboarding_status_for_user,
    get_resume_for_user,
    upload_resume_for_user,
)

router = APIRouter(prefix="/me", tags=["resume"])


@router.get("/resume", response_model=ResumeProfileResponse)
async def get_resume(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ResumeProfileResponse:
    res = await get_resume_for_user(session, user.id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return res


@router.get("/onboarding/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> OnboardingStatusResponse:
    return await get_onboarding_status_for_user(session, user.id)


@router.post("/resume/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ResumeAnalyzeResponse:
    try:
        text = await analyze_resume_for_user(session, user.id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return ResumeAnalyzeResponse(analysis=text)


@router.post("/resume", response_model=ResumeProfileResponse)
async def upload_resume(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
    file: UploadFile = File(...),
) -> ResumeProfileResponse:
    content = await file.read()
    try:
        return await upload_resume_for_user(
            session,
            user.id,
            content,
            file.filename or "resume.pdf",
            file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
