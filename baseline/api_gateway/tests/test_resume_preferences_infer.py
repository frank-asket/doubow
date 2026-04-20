from services.resume_service import infer_preferences_from_parsed_profile


def test_infer_empty_profile_emits_nothing_meaningful():
    assert infer_preferences_from_parsed_profile({}) == {}


def test_infer_headline_skills_and_seniority():
    out = infer_preferences_from_parsed_profile(
        {
            "headline": "Staff ML Engineer",
            "experience_years": 10,
            "skills": ["Python", "PyTorch", "CUDA"],
            "top_skills": ["Python", "PyTorch"],
        }
    )
    assert out["target_role"] == "Staff ML Engineer"
    assert out["skills"] == ["Python", "PyTorch"]
    assert out["seniority"] == "Lead"


def test_infer_archetype_when_no_headline():
    out = infer_preferences_from_parsed_profile(
        {
            "headline": "",
            "archetypes": ["Platform engineer", "Backend"],
            "experience_years": 3,
            "skills": ["Go"],
        }
    )
    assert out["target_role"] == "Platform engineer"
    assert out["seniority"] == "Mid"
