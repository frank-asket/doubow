"""Resume eligibility for stuck LangGraph autopilot runs."""

import pytest

from config import settings
from models.autopilot_run import AutopilotRun
from models.user import User
from services.autopilot_resume import validate_resume_eligibility


@pytest.mark.asyncio
async def test_resume_requires_running_status(db_session):
    db_session.add(User(id="user_resume_1", email="r1@example.com"))
    db_session.add(
        AutopilotRun(
            id="run_done_1",
            user_id="user_resume_1",
            status="done",
            scope="all",
            graph_checkpoint={"v": 1},
        )
    )
    await db_session.commit()

    _, reason = await validate_resume_eligibility(
        db_session, user_id="user_resume_1", run_id="run_done_1"
    )
    assert reason and "not running" in reason.lower()


@pytest.mark.asyncio
async def test_resume_requires_checkpoint_when_langgraph_checkpoint_enabled(db_session, monkeypatch):
    monkeypatch.setattr(settings, "use_langgraph_autopilot", True)
    monkeypatch.setattr(settings, "use_langgraph_autopilot_checkpoint", True)

    db_session.add(User(id="user_resume_2", email="r2@example.com"))
    db_session.add(
        AutopilotRun(
            id="run_no_ck",
            user_id="user_resume_2",
            status="running",
            scope="all",
            graph_checkpoint=None,
        )
    )
    await db_session.commit()

    _, reason = await validate_resume_eligibility(db_session, user_id="user_resume_2", run_id="run_no_ck")
    assert reason and "checkpoint" in reason.lower()


@pytest.mark.asyncio
async def test_resume_allowed_with_checkpoint(db_session, monkeypatch):
    monkeypatch.setattr(settings, "use_langgraph_autopilot", True)
    monkeypatch.setattr(settings, "use_langgraph_autopilot_checkpoint", True)

    db_session.add(User(id="user_resume_3", email="r3@example.com"))
    db_session.add(
        AutopilotRun(
            id="run_ok_ck",
            user_id="user_resume_3",
            status="running",
            scope="all",
            graph_checkpoint={"v": 1, "state": {}, "next_resume_entry": "process_items"},
        )
    )
    await db_session.commit()

    row, reason = await validate_resume_eligibility(db_session, user_id="user_resume_3", run_id="run_ok_ck")
    assert row is not None
    assert reason == ""
