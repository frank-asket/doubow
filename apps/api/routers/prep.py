from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/me/prep", tags=["prep"])


class PrepSessionResponse(BaseModel):
    id: str
    questions: list[str]
    star_stories: list[dict]
    company_brief: str


@router.get("", response_model=PrepSessionResponse)
async def list_prep(application_id: str = Query(...)) -> PrepSessionResponse:
    return PrepSessionResponse(
        id=f"prep_{application_id}",
        questions=[
            "Walk me through a production RAG system you built.",
            "How do you handle latency vs retrieval accuracy trade-offs?",
        ],
        star_stories=[],
        company_brief="Company focuses on agentic workflows and high-quality model operations.",
    )
