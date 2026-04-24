import pytest

from services.openrouter import normalize_openrouter_model_id


@pytest.fixture(autouse=True)
def _reset_openrouter_circuit_state():
    from services import openrouter as openrouter_service

    openrouter_service._reset_openrouter_circuit_state_for_tests()
    yield
    openrouter_service._reset_openrouter_circuit_state_for_tests()


def test_preserves_provider_slash_format():
    assert normalize_openrouter_model_id("anthropic/claude-sonnet-4.6") == "anthropic/claude-sonnet-4.6"


def test_prepends_anthropic_for_bare_claude_ids():
    assert normalize_openrouter_model_id("claude-sonnet-4-20250514") == "anthropic/claude-sonnet-4-20250514"
