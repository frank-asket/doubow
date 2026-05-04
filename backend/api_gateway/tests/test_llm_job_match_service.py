"""Tests for LLM job fit (debate + legacy)."""

from types import SimpleNamespace

import pytest

from config import settings
from services import llm_job_match_service as m


def _job_stub(**kwargs):
    return SimpleNamespace(
        title="Engineer",
        company="Co",
        location="Remote",
        description=kwargs.get("description", "Build things"),
        description_clean=None,
        description_raw=None,
    )


@pytest.mark.asyncio
async def test_llm_fit_signal_legacy_path_when_debate_disabled(monkeypatch):
    job = _job_stub()
    profile = {"headline": "SWE", "summary": "Python", "skills": ["python"]}

    monkeypatch.setattr(settings, "use_llm_fit_debate", False)

    calls: list[str] = []

    async def _fake_chat(*, user_message: str, system_message: str, use_case: str | None = None, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(use_case or "")
        return '{"fit_score": 4.2, "reasons": ["skills match"]}'

    monkeypatch.setattr(m, "chat_completion", _fake_chat)

    fit, reasons, risks = await m.llm_fit_signal(profile, job)
    assert fit == 4.2
    assert reasons == ["skills match"]
    assert risks == []
    assert calls == ["deep"]


@pytest.mark.asyncio
async def test_llm_fit_signal_debate_three_calls(monkeypatch):
    job = _job_stub()
    profile = {"headline": "SWE", "summary": "Python", "skills": ["python"]}

    monkeypatch.setattr(settings, "use_llm_fit_debate", True)

    responses = iter(
        [
            '{"arguments": ["Strong Python match", "Remote OK"], "strength": 4.5}',
            '{"concerns": ["No K8s listed"], "severity": 2.0}',
            '{"fit_score": 4.0, "reasons": ["Good overlap"], "risk_flags": ["K8s gap"]}',
        ]
    )

    async def _fake_chat(*, user_message: str, system_message: str, use_case: str | None = None, **kwargs):  # type: ignore[no-untyped-def]
        assert use_case == "deep"
        return next(responses)

    monkeypatch.setattr(m, "chat_completion", _fake_chat)

    fit, reasons, risks = await m.llm_fit_signal(profile, job)
    assert fit == 4.0
    assert reasons == ["Good overlap"]
    assert risks == ["K8s gap"]
