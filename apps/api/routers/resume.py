from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/me", tags=["resume"])


class ResumeResponse(BaseModel):
    id: str
    storage_path: str
    parsed_profile: dict
    preferences: dict
    version: int


@router.get("/resume", response_model=ResumeResponse)
async def get_resume() -> ResumeResponse:
    return ResumeResponse(
        id="resume_001",
        storage_path="resumes/dev-user/resume-v1.pdf",
        parsed_profile={"top_skills": ["RAG", "Python", "FastAPI"]},
        preferences={"target_role": "AI/ML Engineer", "location": "Remote / Europe", "seniority": "Senior"},
        version=1,
    )
