"""Prompt profiles include grounding and channel-specific instructions."""

from services.llm_prompts import (
    GROUNDING_RULES,
    ORCHESTRATOR_SYSTEM,
    draft_email_system,
    draft_linkedin_system,
    normalize_orchestrator_response,
    prep_json_only_system,
    resume_profile_analysis_system,
)


def test_grounding_rules_nonempty():
    assert "inventing" in GROUNDING_RULES.lower() or "ground" in GROUNDING_RULES.lower()


def test_draft_prompts_include_grounding():
    assert GROUNDING_RULES.split()[0] in draft_email_system()
    assert GROUNDING_RULES.split()[0] in draft_linkedin_system()


def test_prep_json_system_requires_json_only():
    s = prep_json_only_system()
    assert "json" in s.lower()
    assert "markdown" in s.lower() or "fences" in s.lower()


def test_resume_analysis_mentions_next_steps():
    s = resume_profile_analysis_system()
    assert "next step" in s.lower()


def test_orchestrator_prompt_requires_structured_sections():
    s = ORCHESTRATOR_SYSTEM
    assert "summary:" in s.lower()
    assert "recommended actions:" in s.lower()
    assert "why:" in s.lower()
    assert "next step:" in s.lower()


def test_normalize_orchestrator_response_from_freeform_text():
    normalized = normalize_orchestrator_response(
        "You should focus on fintech PM roles this week.\n"
        "Actions:\n"
        "1. Apply to Stripe role\n"
        "2. Tailor resume bullets\n"
    )
    assert "Summary:" in normalized
    assert "Recommended Actions:" in normalized
    assert "Why:" in normalized
    assert "Next Step:" in normalized
    assert "- Apply to Stripe role" in normalized


def test_normalize_orchestrator_response_preserves_section_content():
    normalized = normalize_orchestrator_response(
        "Summary: Strong fit for product strategy roles.\n"
        "Recommended Actions: Update headline for fintech focus.\n"
        "Why: Recruiters scan headline first.\n"
        "Next Step: Rewrite your headline today."
    )
    assert "- Strong fit for product strategy roles." in normalized
    assert "- Update headline for fintech focus." in normalized
    assert "- Recruiters scan headline first." in normalized
    assert "- Rewrite your headline today." in normalized
