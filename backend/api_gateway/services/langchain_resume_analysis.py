"""LangChain-based structured resume analysis (feature-flagged)."""

from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from schemas.resume import ParsedProfileModel, UserPreferencesModel
from services.openrouter import chat_completion


class ResumeAnalysisStructured(BaseModel):
    summary: str = Field(description="Short overall evaluation of profile fit.")
    strengths: list[str] = Field(default_factory=list, description="Top 3-5 strengths.")
    gaps: list[str] = Field(default_factory=list, description="Top 3-5 gaps.")
    next_steps: list[str] = Field(default_factory=list, description="3-5 concrete next steps.")


def _as_text(result: ResumeAnalysisStructured) -> str:
    lines = [f"Summary: {result.summary.strip()}"]
    if result.strengths:
        lines.append("Strengths: " + "; ".join(s.strip() for s in result.strengths if s.strip()))
    if result.gaps:
        lines.append("Gaps: " + "; ".join(s.strip() for s in result.gaps if s.strip()))
    if result.next_steps:
        lines.append("Next steps: " + "; ".join(s.strip() for s in result.next_steps if s.strip()))
    return "\n\n".join(lines)


async def analyze_resume_with_langchain(parsed: ParsedProfileModel, prefs: UserPreferencesModel) -> str:
    parser = PydanticOutputParser(pydantic_object=ResumeAnalysisStructured)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a concise career coach. Return only valid JSON matching the schema.",
            ),
            (
                "human",
                "Parsed profile:\n{parsed_json}\n\nPreferences:\n{prefs_json}\n\n{format_instructions}",
            ),
        ]
    )
    messages = prompt.format_messages(
        parsed_json=parsed.model_dump_json(indent=2),
        prefs_json=prefs.model_dump_json(indent=2),
        format_instructions=parser.get_format_instructions(),
    )
    system_message = str(messages[0].content)
    user_message = str(messages[1].content)
    raw = await chat_completion(system_message=system_message, user_message=user_message)
    structured = parser.parse(raw)
    return _as_text(structured)
