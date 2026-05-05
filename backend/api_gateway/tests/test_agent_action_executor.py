from types import SimpleNamespace

import pytest

from services.agent_action_approvals import (
    ApprovalActionError,
    approve_outbound_draft_action,
    reject_outbound_draft_action,
)
from services.agent_action_executor import AgentActionCall, AgentActionPolicyError, execute_action, infer_action_from_message


def test_infer_pipeline_run_slash_flags() -> None:
    a1 = infer_action_from_message("/pipeline-run")
    assert a1 is not None
    assert a1.action == "run_job_search_pipeline"
    assert a1.trigger_catalog_refresh is False
    assert a1.persist_feedback_learning is False
    a2 = infer_action_from_message("/pipeline-run --refresh --persist-feedback")
    assert a2 is not None
    assert a2.trigger_catalog_refresh is True
    assert a2.persist_feedback_learning is True


def test_infer_pipeline_run_natural_language() -> None:
    action = infer_action_from_message("Please run job search pipeline")
    assert action is not None
    assert action.action == "run_job_search_pipeline"


def test_infer_pipeline_summary_still_snapshot_not_runner() -> None:
    action = infer_action_from_message("pipeline summary with status mix")
    assert action is not None
    assert action.action == "get_pipeline_snapshot"


def test_infer_pipeline_action_from_slash_command() -> None:
    action = infer_action_from_message("/pipeline")
    assert action is not None
    assert action.action == "get_pipeline_snapshot"


def test_infer_pipeline_action_from_natural_language() -> None:
    action = infer_action_from_message("Can you give me a pipeline summary with status mix?")
    assert action is not None
    assert action.action == "get_pipeline_snapshot"


def test_infer_pending_approvals_with_limit() -> None:
    action = infer_action_from_message("show top 7 pending approvals")
    assert action is not None
    assert action.action == "list_pending_approvals"
    assert action.limit == 7


def test_infer_job_matches_with_limit() -> None:
    action = infer_action_from_message("show top 4 job matches")
    assert action is not None
    assert action.action == "get_job_matches"
    assert action.limit == 4


def test_infer_application_detail_from_id() -> None:
    action = infer_action_from_message("show application detail for app_123abc")
    assert action is not None
    assert action.action == "get_application_detail"
    assert action.application_id == "app_123abc"


def test_infer_application_detail_latest_without_id() -> None:
    action = infer_action_from_message("/application latest status")
    assert action is not None
    assert action.action == "get_application_detail"
    assert action.application_id is None


def test_infer_create_draft_with_application_id() -> None:
    action = infer_action_from_message("create draft for app_abc123")
    assert action is not None
    assert action.action == "create_draft_for_application"
    assert action.application_id == "app_abc123"


def test_infer_create_draft_without_application_id() -> None:
    action = infer_action_from_message("/draft please create one")
    assert action is not None
    assert action.action == "create_draft_for_application"
    assert action.application_id is None


def test_infer_returns_none_for_generic_message() -> None:
    action = infer_action_from_message("How should I position my resume for staff roles?")
    assert action is None


def test_infer_recompute_keyword() -> None:
    action = infer_action_from_message("Please rescore my matches after my edits")
    assert action is not None
    assert action.action == "recompute_job_scores"


def test_infer_prep_generate_before_summary() -> None:
    action = infer_action_from_message("generate prep for app_xyz789")
    assert action is not None
    assert action.action == "generate_prep_for_application"


def test_infer_autopilot_runs() -> None:
    action = infer_action_from_message("show recent autopilot run status")
    assert action is not None
    assert action.action == "list_recent_autopilot_runs"


def test_infer_queue_slash_command() -> None:
    action = infer_action_from_message("/queue jb_cat_001 email")
    assert action is not None
    assert action.action == "queue_job_to_pipeline"
    assert action.job_id == "jb_cat_001"
    assert action.channel == "email"


def test_infer_dismiss_slash() -> None:
    action = infer_action_from_message("/dismiss jb_drop_1")
    assert action is not None
    assert action.action == "dismiss_job_from_discover"
    assert action.job_id == "jb_drop_1"


def test_infer_approve_reject_uuids() -> None:
    uid = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    a1 = infer_action_from_message(f"/approve {uid}")
    assert a1 is not None
    assert a1.action == "approve_outbound_draft"
    assert a1.approval_id == uid
    a2 = infer_action_from_message(f"/reject {uid}")
    assert a2 is not None
    assert a2.action == "reject_outbound_draft"
    assert a2.approval_id == uid


@pytest.mark.asyncio
async def test_approve_outbound_draft_action_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_approve(session, user_id, approval_id, edited_body, idempotency_key):
        captured["approve_args"] = (session, user_id, approval_id, edited_body, idempotency_key)
        return SimpleNamespace(status="approved", queued_send=True, send_task_id="task-123")

    def _fake_schedule(*, approval_id: str, user_id: str, queued_send: bool, send_task_id: str | None) -> None:
        captured["schedule_args"] = (approval_id, user_id, queued_send, send_task_id)

    monkeypatch.setattr("services.agent_action_approvals.approve_approval_service", _fake_approve)
    monkeypatch.setattr("services.agent_action_approvals.schedule_post_approve_dispatch", _fake_schedule)

    body = await approve_outbound_draft_action(
        session=SimpleNamespace(),
        user_id="usr_1",
        approval_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    )

    assert "Approved outbound draft" in body
    assert "Outbound send has been queued" in body
    assert captured["schedule_args"] == (
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "usr_1",
        True,
        "task-123",
    )


@pytest.mark.asyncio
async def test_approve_outbound_draft_action_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_approve(*args, **kwargs):
        raise ValueError("missing")

    monkeypatch.setattr("services.agent_action_approvals.approve_approval_service", _fake_approve)

    with pytest.raises(ApprovalActionError) as exc:
        await approve_outbound_draft_action(
            session=SimpleNamespace(),
            user_id="usr_1",
            approval_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        )
    assert exc.value.code == "approval_not_found"


@pytest.mark.asyncio
async def test_reject_outbound_draft_action_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_reject(*args, **kwargs):
        raise ValueError("missing")

    monkeypatch.setattr("services.agent_action_approvals.reject_approval_service", _fake_reject)

    with pytest.raises(ApprovalActionError) as exc:
        await reject_outbound_draft_action(
            session=SimpleNamespace(),
            user_id="usr_1",
            approval_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        )
    assert exc.value.code == "approval_not_found"


@pytest.mark.asyncio
async def test_execute_action_maps_approval_error_to_policy_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_approve_action(*, session, user_id, approval_id):
        raise ApprovalActionError(code="approval_not_found", detail="Approval not found")

    monkeypatch.setattr("services.agent_action_executor.approve_outbound_draft_action", _fake_approve_action)

    with pytest.raises(AgentActionPolicyError) as exc:
        await execute_action(
            session=SimpleNamespace(),
            user_id="usr_1",
            call=AgentActionCall(action="approve_outbound_draft", approval_id="missing"),
        )
    assert exc.value.action == "approve_outbound_draft"
    assert exc.value.code == "approval_not_found"
