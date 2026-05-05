from types import SimpleNamespace

import pytest

from services.agent_action_executor import AgentActionCall, AgentActionPolicyError, execute_action
from services.agent_action_pipeline import (
    PipelineActionError,
    dismiss_job_from_discover_action,
    queue_job_to_pipeline_action,
    run_job_search_pipeline_action,
)


@pytest.mark.asyncio
async def test_run_job_search_pipeline_action_rejects_invalid_stage() -> None:
    with pytest.raises(PipelineActionError) as exc:
        await run_job_search_pipeline_action(
            session=SimpleNamespace(),
            user_id="usr_1",
            pipeline_stages=["not_a_stage"],
            trigger_catalog_refresh=False,
            persist_feedback_learning=False,
            catalog_preset="hourly",
            include_legacy_connectors=False,
            include_scrapling=True,
            resume_aligned_catalog=True,
            settings=SimpleNamespace(),
        )
    assert exc.value.code == "invalid_stage"


@pytest.mark.asyncio
async def test_queue_job_to_pipeline_action_requires_job_id() -> None:
    with pytest.raises(PipelineActionError) as exc:
        await queue_job_to_pipeline_action(
            session=SimpleNamespace(),
            user_id="usr_1",
            job_id=None,
            channel="email",
        )
    assert exc.value.code == "job_id_required"


@pytest.mark.asyncio
async def test_dismiss_job_from_discover_action_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_dismiss(*args, **kwargs):
        raise LookupError("missing")

    monkeypatch.setattr("services.agent_action_pipeline.dismiss_job_for_user", _fake_dismiss)

    with pytest.raises(PipelineActionError) as exc:
        await dismiss_job_from_discover_action(
            session=SimpleNamespace(),
            user_id="usr_1",
            job_id="jb_missing",
        )
    assert exc.value.code == "job_not_found"


@pytest.mark.asyncio
async def test_execute_action_maps_pipeline_error_to_policy_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_run_pipeline_action(**kwargs):
        raise PipelineActionError(code="invalid_stage", detail="bad stage")

    monkeypatch.setattr("services.agent_action_executor.run_job_search_pipeline_action", _fake_run_pipeline_action)

    with pytest.raises(AgentActionPolicyError) as exc:
        await execute_action(
            session=SimpleNamespace(),
            user_id="usr_1",
            call=AgentActionCall(action="run_job_search_pipeline", pipeline_stages=["bad"]),
        )

    assert exc.value.action == "run_job_search_pipeline"
    assert exc.value.code == "invalid_stage"
