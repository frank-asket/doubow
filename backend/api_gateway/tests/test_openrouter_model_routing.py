import pytest

from config import settings
from services.openrouter import normalize_openrouter_model_id


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
