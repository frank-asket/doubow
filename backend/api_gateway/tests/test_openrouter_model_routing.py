import pytest
import httpx

from config import settings
from services.openrouter import normalize_openrouter_model_id


@pytest.fixture(autouse=True)
def _reset_openrouter_circuit_state():
    from services import openrouter as openrouter_service

    openrouter_service._reset_openrouter_circuit_state_for_tests()
    yield
    openrouter_service._reset_openrouter_circuit_state_for_tests()


def test_resolve_openrouter_model_tier_defaults(monkeypatch):
    """Qwen3-class global + drafts, Claude chat, DeepSeek R1 prep; resume inherits global."""
    monkeypatch.setattr(settings, "openrouter_model", "qwen/qwen3-32b")
    monkeypatch.setattr(settings, "openrouter_model_chat", "anthropic/claude-sonnet-4.6")
    monkeypatch.setattr(settings, "openrouter_model_drafts", "qwen/qwen3-8b")
    monkeypatch.setattr(settings, "openrouter_model_prep", "deepseek/deepseek-r1-0528")
    monkeypatch.setattr(settings, "openrouter_model_resume", None)

    assert settings.resolve_openrouter_model("chat") == "anthropic/claude-sonnet-4.6"
    assert settings.resolve_openrouter_model("drafts") == "qwen/qwen3-8b"
    assert settings.resolve_openrouter_model("prep") == "deepseek/deepseek-r1-0528"
    assert settings.resolve_openrouter_model("resume") == "qwen/qwen3-32b"


def test_resolve_openrouter_model_deep_quick_override_prep_and_drafts(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_model", "qwen/qwen3-32b")
    monkeypatch.setattr(settings, "openrouter_model_prep", "deepseek/deepseek-r1-0528")
    monkeypatch.setattr(settings, "openrouter_model_drafts", "qwen/qwen3-8b")
    monkeypatch.setattr(settings, "openrouter_model_deep", "anthropic/claude-opus-4")
    monkeypatch.setattr(settings, "openrouter_model_quick", "anthropic/claude-haiku-4")

    assert settings.resolve_openrouter_model("prep") == "anthropic/claude-opus-4"
    assert settings.resolve_openrouter_model("drafts") == "anthropic/claude-haiku-4"
    assert settings.resolve_openrouter_model("deep") == "anthropic/claude-opus-4"
    assert settings.resolve_openrouter_model("quick") == "anthropic/claude-haiku-4"


def test_resolve_openrouter_model_uses_use_case_override(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_model", "anthropic/claude-sonnet-4.6")
    monkeypatch.setattr(settings, "openrouter_model_prep", "openai/gpt-4.1-mini")

    assert settings.resolve_openrouter_model("prep") == "openai/gpt-4.1-mini"
    assert settings.resolve_openrouter_model("chat") == "anthropic/claude-sonnet-4.6"


def test_resolve_openrouter_model_falls_back_to_anthropic(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_model", "")
    monkeypatch.setattr(settings, "anthropic_model", "claude-sonnet-4-20250514")
    monkeypatch.setattr(settings, "openrouter_model_chat", None)

    assert settings.resolve_openrouter_model("chat") == "claude-sonnet-4-20250514"
    assert normalize_openrouter_model_id(settings.resolve_openrouter_model("chat")) == "anthropic/claude-sonnet-4-20250514"


@pytest.mark.asyncio
async def test_openrouter_chat_completion_uses_use_case_model(monkeypatch):
    from services import openrouter as openrouter_service

    monkeypatch.setattr(settings, "openrouter_api_key", "test_key")
    monkeypatch.setattr(settings, "openrouter_api_url", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "openrouter_model", "anthropic/claude-sonnet-4.6")
    monkeypatch.setattr(settings, "openrouter_model_drafts", "openai/gpt-4.1-mini")
    monkeypatch.setattr(settings, "openrouter_max_retries", 1)

    captured: dict[str, object] = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _FakeResponse()

    monkeypatch.setattr(openrouter_service.httpx, "AsyncClient", _FakeClient)

    result = await openrouter_service.chat_completion(
        user_message="hello",
        system_message="system",
        use_case="drafts",
    )

    assert result == "ok"
    assert captured["json"]["model"] == "openai/gpt-4.1-mini"
    assert captured["json"]["temperature"] == 0.45
    assert captured["json"]["max_tokens"] == 900
    assert captured["json"]["top_p"] == 0.9
    assert captured["json"]["frequency_penalty"] == 0.12


@pytest.mark.asyncio
async def test_openrouter_chat_circuit_opens_after_repeated_failures(monkeypatch):
    from services import openrouter as openrouter_service

    openrouter_service._reset_openrouter_circuit_state_for_tests()
    monkeypatch.setattr(settings, "openrouter_api_key", "test_key")
    monkeypatch.setattr(settings, "openrouter_api_url", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "openrouter_model", "anthropic/claude-sonnet-4.6")
    monkeypatch.setattr(settings, "openrouter_max_retries", 1)

    class _FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(openrouter_service.httpx, "AsyncClient", _FailingClient)

    with pytest.raises(httpx.TimeoutException):
        await openrouter_service.chat_completion(user_message="hello", system_message="system", use_case="chat")

    with pytest.raises(httpx.TimeoutException):
        await openrouter_service.chat_completion(user_message="hello", system_message="system", use_case="chat")

    with pytest.raises(RuntimeError, match="circuit temporarily open"):
        await openrouter_service.chat_completion(user_message="hello", system_message="system", use_case="chat")
