"""Central prompts for OpenRouter calls — grounding, tone, and format per use-case.

Prompt bodies live as versioned text under ``api_gateway/prompts/``; this module composes
them and keeps response normalization logic.
"""

from __future__ import annotations

import re

from prompt_loader import load_prompt_text, load_prompt_with_grounding

# Shared anti-hallucination instruction (single source: ``prompts/grounding_rules.txt``).
GROUNDING_RULES = load_prompt_text("grounding_rules.txt")

ORCHESTRATOR_SYSTEM = load_prompt_text("orchestrator_system.txt")


def draft_email_system() -> str:
    return load_prompt_with_grounding("draft_email_system.txt")


def draft_linkedin_system() -> str:
    return load_prompt_with_grounding("draft_linkedin_system.txt")


def prep_json_only_system() -> str:
    return load_prompt_with_grounding("prep_json_only_system.txt")


def prep_assist_company_brief_system() -> str:
    return load_prompt_with_grounding("prep_assist_company_brief_system.txt")


def prep_assist_star_system() -> str:
    return load_prompt_with_grounding("prep_assist_star_system.txt")


def resume_profile_analysis_system() -> str:
    return load_prompt_with_grounding("resume_profile_analysis_system.txt")


def langchain_resume_json_system() -> str:
    return load_prompt_with_grounding("langchain_resume_json_system.txt")


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


def normalize_orchestrator_response_with_meta(text: str) -> tuple[str, bool]:
    """Return normalized output and whether post-processing changed payload shape/content."""
    normalized = normalize_orchestrator_response(text)
    raw = (text or "").strip()
    return normalized, (normalized.strip() != raw)
