from services.openrouter import normalize_openrouter_model_id


def test_preserves_provider_slash_format():
    assert normalize_openrouter_model_id("anthropic/claude-sonnet-4.6") == "anthropic/claude-sonnet-4.6"


def test_prepends_anthropic_for_bare_claude_ids():
    assert normalize_openrouter_model_id("claude-sonnet-4-20250514") == "anthropic/claude-sonnet-4-20250514"
