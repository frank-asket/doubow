"""Prompt profiles include grounding and channel-specific instructions."""

from services.llm_prompts import (
    GROUNDING_RULES,
    draft_email_system,
    draft_linkedin_system,
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
