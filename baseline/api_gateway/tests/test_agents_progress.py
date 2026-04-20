"""Agent status progress derived from DB rows (no fixed decimals)."""

import pytest

from models.autopilot_run import AutopilotRun
from models.user import User
from services.agents_service import _autopilot_run_progress, list_agent_status


def test_autopilot_progress_prefers_item_results_fraction():
    r1 = AutopilotRun(
        id="run_1",
        user_id="u1",
        status="running",
        scope="all",
        item_results=[
            {"application_id": "a1", "status": "success"},
            {"application_id": "a2", "status": "failed"},
        ],
    )
    r2 = AutopilotRun(id="run_2", user_id="u1", status="running", scope="all", item_results=[])
    # Two runs with item lists: first is 0.5 success rate; second empty list ignored for item path — run_2 falls through to status
    assert _autopilot_run_progress([r1]) == pytest.approx(0.5)
    # Mixed: r1 has items (0.5), r2 no items → only r1 contributes to item_fractions
    assert _autopilot_run_progress([r1, r2]) == pytest.approx(0.5)


def test_autopilot_progress_falls_back_to_running_share():
    runs = [
        AutopilotRun(id="r_a", user_id="u1", status="queued", scope="all", item_results=None),
        AutopilotRun(id="r_b", user_id="u1", status="running", scope="all", item_results=None),
    ]
    assert _autopilot_run_progress(runs) == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_list_agent_status_orchestrator_progress_from_totals(db_session):
    """When some approvals are non-pending, progress reflects resolved / total."""
    from models.application import Application
    from models.approval import Approval
    from models.job import Job

    db_session.add(User(id="u_orch", email="orch@example.com"))
    db_session.add(
        Job(
            id="j_orch",
            source="manual",
            external_id="e1",
            title="T",
            company="C",
            location="Remote",
            description="d",
            url="https://example.com/j",
        )
    )
    db_session.add(
        Application(
            id="app_a",
            user_id="u_orch",
            job_id="j_orch",
            status="saved",
            channel="email",
        )
    )
    db_session.add(
        Application(
            id="app_b",
            user_id="u_orch",
            job_id="j_orch",
            status="saved",
            channel="email",
        )
    )
    db_session.add(
        Approval(
            id="ap_pend",
            user_id="u_orch",
            application_id="app_a",
            type="cover_letter",
            channel="email",
            subject="s",
            draft_body="body",
            status="pending",
        )
    )
    db_session.add(
        Approval(
            id="ap_done",
            user_id="u_orch",
            application_id="app_b",
            type="cover_letter",
            channel="email",
            subject="s2",
            draft_body="body2",
            status="approved",
        )
    )
    await db_session.commit()

    agents = await list_agent_status(db_session, "u_orch")
    orch = next(a for a in agents if a.name == "orchestrator")
    assert orch.status == "running"
    assert orch.progress == pytest.approx(0.5)
    assert orch.items_processed == 1
