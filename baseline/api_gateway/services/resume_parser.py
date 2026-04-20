async def parse_resume(file_bytes: bytes, mime: str) -> dict:
    """Extract structured profile data from resume bytes.

    Stub implementation — swap for PDF/DOC parsing or an LLM extraction pipeline.
    """
    _ = file_bytes, mime
    return {
        "name": "",
        "headline": "",
        "experience_years": 0,
        "skills": [],
        "top_skills": [],
        "archetypes": [],
        "gaps": ["Resume text extraction is not enabled yet; add roles and impact for stronger matching."],
        "summary": "Your file was stored. Connect a parser or LLM to populate skills and experience automatically.",
    }
