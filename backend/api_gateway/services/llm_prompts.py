"""Central prompts for OpenRouter calls — grounding, tone, and format per use-case.

Keeps prompt/model interaction quality consistent across drafts, prep, resume, and orchestrator chat.
"""

from __future__ import annotations
import re

# Shared anti-hallucination instruction (prepend or append to system prompts).
GROUNDING_RULES = (
    "Ground every substantive claim in the materials provided by the user or system context. "
    "If something is unknown from that context, say so briefly instead of inventing company facts, "
    "metrics, employers, or credentials."
)

ORCHESTRATOR_SYSTEM = (
    "You are Doubow's unified assistant (orchestrator). The user has one chat for everything career-related: "
    "job discovery and fit, pipeline and applications, resume updates, outbound drafts and approvals, "
    "interview prep, follow-ups, and general strategy. Infer intent from each message and answer directly; "
    "do not ask them to switch to another screen unless something truly requires it. Be concise and actionable.\n\n"
    "Output format contract (always follow this structure unless user explicitly asks for a different format):\n"
    "Summary:\n"
    "- 1-2 bullets with the direct answer/result.\n"
    "Recommended Actions:\n"
    "- 2-4 concrete steps the user can take now, ordered by impact.\n"
    "Why:\n"
    "- 1-2 bullets explaining the reasoning and tradeoffs.\n"
    "Next Step:\n"
    "- Exactly one immediate next step phrased as an action.\n\n"
    "Formatting constraints:\n"
    "- Use plain text only (no markdown tables, no code fences).\n"
    "- Keep each bullet concise and specific.\n"
    "- If context is missing, say what is unknown briefly under Summary, then continue with best-effort guidance."
)


def draft_email_system() -> str:
    return (
        "You write concise, professional outbound emails for job applications. "
        + GROUNDING_RULES
        + " Match tone to the posting: startup vs enterprise when inferable from the description. "
        "Use plain language; avoid clichés and filler. "
        "For email output: first line must be exactly `SUBJECT: <subject>` then a blank line, then the body."
    )


def draft_linkedin_system() -> str:
    return (
        "You write short LinkedIn outreach notes for job seekers. "
        + GROUNDING_RULES
        + " Maximum ~1200 characters. No subject line. Warm and specific to the role; no spammy cadence."
    )


def prep_json_only_system() -> str:
    return (
        "You help candidates prepare for interviews. Reply with ONLY valid JSON matching the schema described "
        "in the user message — no markdown fences, no commentary before or after. "
        + GROUNDING_RULES
        + " For company_brief, infer cautiously from the posting; label speculation clearly if needed."
    )


def prep_assist_company_brief_system() -> str:
    return (
        "You are Doubow. Write a concise company brief for interview preparation. "
        + GROUNDING_RULES
        + " Prefer signals from the job description; where you use general knowledge about a well-known company, "
        "keep claims conservative."
    )


def prep_assist_star_system() -> str:
    return (
        "You are Doubow, an AI job search assistant. Generate one specific STAR-R interview story. "
        + GROUNDING_RULES
        + " Use plausible metrics only when consistent with the role level; format with clear labels: "
        "Situation, Task, Action, Result, Reflection."
    )


def resume_profile_analysis_system() -> str:
    return (
        "You are a concise career coach. Given structured résumé data and job-search preferences, "
        "write a short profile analysis: strengths, gaps, fit for the stated target role/location, "
        "and 3–5 concrete next steps. Use plain text with short paragraphs or bullet lines; no markdown headings. "
        + GROUNDING_RULES
        + " Base strengths and gaps only on the parsed profile and preferences — do not invent employers or dates."
    )


def langchain_resume_json_system() -> str:
    return (
        "You are a concise career coach. Return only valid JSON matching the schema. "
        + GROUNDING_RULES
    )


_ORCH_SECTION_ALIASES: dict[str, str] = {
    "summary": "summary",
    "recommended actions": "recommended_actions",
    "recommended action": "recommended_actions",
    "recommendations": "recommended_actions",
    "actions": "recommended_actions",
    "action plan": "recommended_actions",
    "why": "why",
    "rationale": "why",
    "reasoning": "why",
    "next step": "next_step",
    "next steps": "next_step",
}


def _normalize_bullet_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        if line:
            out.append(f"- {line}")
    return out


def normalize_orchestrator_response(text: str) -> str:
    """Normalize LLM output to Doubow's 4-section chat contract."""
    raw = (text or "").strip()
    raw = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    lines = [ln.rstrip() for ln in raw.splitlines()]

    sections: dict[str, list[str]] = {
        "summary": [],
        "recommended_actions": [],
        "why": [],
        "next_step": [],
    }
    current: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        heading_match = re.match(r"^#{0,3}\s*([A-Za-z ]+)\s*:\s*(.*)$", stripped)
        if heading_match:
            label = heading_match.group(1).strip().lower()
            remainder = heading_match.group(2).strip()
            key = _ORCH_SECTION_ALIASES.get(label)
            if key:
                current = key
                if remainder:
                    sections[key].append(remainder)
                continue

        bare_heading = stripped.lower().rstrip(":")
        key = _ORCH_SECTION_ALIASES.get(bare_heading)
        if key:
            current = key
            continue

        if current:
            sections[current].append(stripped)
        else:
            sections["summary"].append(stripped)

    if not sections["summary"] and raw:
        first = next((ln.strip() for ln in lines if ln.strip()), "Response generated.")
        sections["summary"] = [first]
    if not sections["recommended_actions"]:
        sections["recommended_actions"] = ["Confirm your priority so I can tailor the plan."]
    if not sections["why"]:
        sections["why"] = ["This order focuses on the highest-impact action first."]
    if not sections["next_step"]:
        first_action = _normalize_bullet_lines(sections["recommended_actions"])[0]
        sections["next_step"] = [first_action.removeprefix("- ").strip()]

    summary = _normalize_bullet_lines(sections["summary"])[:2]
    actions = _normalize_bullet_lines(sections["recommended_actions"])[:4]
    why = _normalize_bullet_lines(sections["why"])[:2]
    next_step = _normalize_bullet_lines(sections["next_step"])[:1]

    return "\n".join(
        [
            "Summary:",
            *summary,
            "Recommended Actions:",
            *actions,
            "Why:",
            *why,
            "Next Step:",
            *next_step,
        ]
    )
