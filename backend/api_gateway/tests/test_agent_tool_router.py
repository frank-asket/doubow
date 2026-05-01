import asyncio

from services.agent_tool_router import plan_agent_action_from_llm


def test_plan_returns_none_when_feature_off(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "orchestrator_llm_tool_routing", False)
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-test")
    out = asyncio.run(plan_agent_action_from_llm("What should I say in a thank-you note?"))
    assert out is None


def test_plan_returns_none_without_api_key(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "orchestrator_llm_tool_routing", True)
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    out = asyncio.run(plan_agent_action_from_llm("Show my pipeline"))
    assert out is None


def test_plan_parses_json_action(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "orchestrator_llm_tool_routing", True)
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-test")

    async def fake_completion(**kwargs):
        return '{"action": "get_pipeline_snapshot", "limit": 5, "application_id": null}'

    monkeypatch.setattr("services.agent_tool_router.chat_completion", fake_completion)
    out = asyncio.run(plan_agent_action_from_llm("Can you summarize where my applications stand?"))
    assert out is not None
    assert out.action == "get_pipeline_snapshot"


def test_plan_none_action(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "orchestrator_llm_tool_routing", True)
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-test")

    async def fake_completion(**kwargs):
        return '{"action": "none", "limit": 5}'

    monkeypatch.setattr("services.agent_tool_router.chat_completion", fake_completion)
    out = asyncio.run(plan_agent_action_from_llm("How do I negotiate salary?"))
    assert out is None
