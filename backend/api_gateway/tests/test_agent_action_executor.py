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
