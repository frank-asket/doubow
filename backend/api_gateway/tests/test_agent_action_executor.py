from services.agent_action_executor import infer_action_from_message


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


def test_infer_returns_none_for_generic_message() -> None:
    action = infer_action_from_message("How should I position my resume for staff roles?")
    assert action is None
