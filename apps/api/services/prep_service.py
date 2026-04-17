from schemas.prep import PrepSessionResponse


async def get_prep_session(application_id: str) -> PrepSessionResponse:
    return PrepSessionResponse(
        id=f"prep_{application_id}",
        questions=[
            "Walk me through a production RAG system you built.",
            "How do you handle latency vs retrieval accuracy trade-offs?",
        ],
        star_stories=[],
        company_brief="Company focuses on agentic workflows and high-quality model operations.",
    )
