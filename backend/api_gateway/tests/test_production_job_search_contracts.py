"""Contract tests for job-search pipeline + feedback learning (CI / pre-release).

Covers the same invariants as manual production verification; run:

  make -C backend api-test-job-search-contracts
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from routers import users
from services.agent_action_executor import infer_action_from_message
from services.agent_tools_catalog import AGENT_TOOLS
from prometheus_client import REGISTRY, generate_latest

from services.metrics import observe_matching_blend_score_sync


def test_contract_capabilities_include_pipeline_runner() -> None:
    names = [t.name for t in AGENT_TOOLS]
    assert "run_job_search_pipeline" in names
    assert "recompute_job_scores" in names


def test_contract_infer_pipeline_run_slash_and_flags() -> None:
    a = infer_action_from_message("/pipeline-run")
    assert a is not None
    assert a.action == "run_job_search_pipeline"
    assert a.trigger_catalog_refresh is False
    p = infer_action_from_message("/pipeline-run --refresh --persist-feedback")
    assert p is not None
    assert p.trigger_catalog_refresh is True
    assert p.persist_feedback_learning is True


def test_contract_infer_pipeline_run_natural_language() -> None:
    a = infer_action_from_message("Please run job search pipeline")
    assert a is not None
    assert a.action == "run_job_search_pipeline"


def test_contract_matching_blend_metric_exposed_after_observe() -> None:
    """After observe_matching_blend_score_sync, /metrics exposition includes the blend counter."""
    observe_matching_blend_score_sync(has_feedback_learning=False, personalized_blend=False)
    observe_matching_blend_score_sync(has_feedback_learning=True, personalized_blend=True)
    exposed = generate_latest(REGISTRY).decode()
    assert "doubow_matching_blend_score_sync_total" in exposed


@pytest.mark.asyncio
async def test_contract_feedback_learning_debug_not_exposed_in_production(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    user = User(id="user_contract_prod", email="contract@example.com")
    db_session.add(user)
    await db_session.commit()

    app = FastAPI()
    app.include_router(users.router, prefix="/v1")

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return user

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_authenticated_user] = _override_user

    with TestClient(app) as client:
        assert client.get("/v1/me/preferences/feedback-learning").status_code == 404
        assert client.delete("/v1/me/preferences/feedback-learning").status_code == 404
