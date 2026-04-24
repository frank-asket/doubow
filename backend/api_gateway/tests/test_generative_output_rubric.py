"""Golden-set style tests for ``generative_quality_rubric`` — CI-enforceable pass/fail without live LLM calls."""

from services.generative_quality_rubric import GenerativeRubricResult, assess_generative_text

_GOOD_CHAT = "Here are three roles worth a closer look given your PM background and remote preference."
_GOOD_DRAFTS = (
    "Dear Hiring Manager,\n\n"
    "I am writing to express interest in the Senior Product role at Acme. "
    "In my last role I led discovery for a B2B analytics product, shipped experiments weekly, "
    "and partnered with sales on activation metrics that improved retention by double digits. "
    "I would welcome the chance to discuss how that experience maps to your roadmap.\n\n"
    "Best regards"
)
_GOOD_PREP = (
    "Company context: Acme is growing the self-serve funnel; expect questions on experimentation, "
    "stakeholder alignment, and how you prioritize when data is ambiguous. "
    "Prepare two STAR stories on conflict resolution and one on a failed launch you recovered."
)

_GOOD_RESUME = (
    "Summary: Product leader with 8+ years shipping B2B SaaS; strengths in discovery, metrics, and cross-functional execution. "
    "Recent impact: reduced time-to-value by 30% via onboarding redesign."
)


def test_rubric_passes_plausible_outputs_per_use_case():
    assert assess_generative_text(_GOOD_CHAT, use_case="chat").passed is True
    assert assess_generative_text(_GOOD_DRAFTS, use_case="drafts").passed is True
    assert assess_generative_text(_GOOD_PREP, use_case="prep").passed is True
    assert assess_generative_text(_GOOD_RESUME, use_case="resume").passed is True


def test_rubric_fails_empty_and_whitespace():
    r = assess_generative_text("", use_case="chat")
    assert r.passed is False
    assert any("empty" in v.lower() for v in r.violations)

    r2 = assess_generative_text("   \n\t  ", use_case="prep")
    assert r2.passed is False


def test_rubric_fails_too_short_for_use_case():
    r = assess_generative_text("short", use_case="drafts")
    assert r.passed is False
    assert any("shorter than minimum" in v for v in r.violations)


def test_rubric_fails_excessive_repetition():
    sentence = "This is the same filler sentence repeated for testing purposes only."
    blob = " ".join([sentence] * 12)
    r = assess_generative_text(blob, use_case="chat")
    assert r.passed is False
    assert any("repetition" in v.lower() for v in r.violations)


def test_rubric_defaults_unknown_use_case_to_default_min():
    # default min is 20 — medium string should pass
    mid = "x" * 25
    assert assess_generative_text(mid, use_case="unknown_xyz").passed is True


def test_result_dataclass_structure():
    r: GenerativeRubricResult = assess_generative_text(_GOOD_CHAT, use_case="chat")
    assert isinstance(r.violations, list)
    assert r.use_case == "chat"
