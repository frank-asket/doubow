from fastapi import APIRouter
from schemas.resume import ResumeResponse
from services.resume_service import get_resume as get_resume_service

router = APIRouter(prefix="/me", tags=["resume"])


@router.get("/resume", response_model=ResumeResponse)
async def get_resume() -> ResumeResponse:
    return await get_resume_service()
