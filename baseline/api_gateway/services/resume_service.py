from schemas.resume import ResumeResponse


async def get_resume() -> ResumeResponse:
    return ResumeResponse(
        id="resume_001",
        storage_path="resumes/dev-user/resume-v1.pdf",
        parsed_profile={"top_skills": ["RAG", "Python", "FastAPI"]},
        preferences={"target_role": "AI/ML Engineer", "location": "Remote / Europe", "seniority": "Senior"},
        version=1,
    )
