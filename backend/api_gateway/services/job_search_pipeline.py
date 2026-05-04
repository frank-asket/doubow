"""
Multi-stage job search pipeline.

Maps modular agents to existing Doubow services without replacing them:
  data_collection  → catalog ingest + env readiness
  resume_profile   → latest parsed resume + preferences
  job_matching     → score recompute for the user
  outbound_application → approvals + pipeline applications snapshot
  feedback         → application status distribution (loop-closing hook)
"""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from models.application import Application
from models.approval import Approval
from models.resume import Resume
from schemas.job_search_pipeline import (
    JobSearchPipelineRunRequest,
    JobSearchPipelineRunResponse,
    JobSearchPipelineStageId,
    PipelineStageOutcome,
)
from services.job_search_feedback import compute_feedback_snapshot
from services.jobs_service import recompute_job_scores_for_user
from services.resume_catalog_params import provider_params_from_user_resume
from services.resume_service import (
    merge_preferences_dicts,
    normalize_parsed_profile_dict,
    persist_feedback_learning_snapshot,
)

logger = logging.getLogger(__name__)

_DEFAULT_ORDER: tuple[JobSearchPipelineStageId, ...] = (
    JobSearchPipelineStageId.data_collection,
    JobSearchPipelineStageId.resume_profile,
    JobSearchPipelineStageId.job_matching,
    JobSearchPipelineStageId.outbound_application,
    JobSearchPipelineStageId.feedback,
)


class JobSearchPipelineCoordinator:
    async def run(
        self,
        session: AsyncSession,
        settings: Settings,
        user_id: str,
        body: JobSearchPipelineRunRequest,
    ) -> JobSearchPipelineRunResponse:
        trace_id = str(uuid.uuid4())
        order = list(body.stages) if body.stages else list(_DEFAULT_ORDER)
        outcomes: list[PipelineStageOutcome] = []

        for stage in order:
            try:
                if stage == JobSearchPipelineStageId.data_collection:
                    outcomes.append(await self._data_collection(session, settings, user_id, body, trace_id))
                elif stage == JobSearchPipelineStageId.resume_profile:
                    outcomes.append(await self._resume_profile(session, user_id))
                elif stage == JobSearchPipelineStageId.job_matching:
                    outcomes.append(await self._job_matching(session, user_id))
                elif stage == JobSearchPipelineStageId.outbound_application:
                    outcomes.append(await self._outbound_application(session, user_id))
                elif stage == JobSearchPipelineStageId.feedback:
                    outcomes.append(await self._feedback(session, user_id, body, trace_id))
                else:  # pragma: no cover
                    outcomes.append(
                        PipelineStageOutcome(
                            stage=stage,
                            ok=False,
                            summary="Unknown stage",
                            error="unknown_stage",
                        )
                    )
            except Exception as exc:  # pragma: no cover - stage handlers are defensive
                logger.exception("pipeline stage failed trace=%s stage=%s", trace_id, stage)
                outcomes.append(
                    PipelineStageOutcome(
                        stage=stage,
                        ok=False,
                        summary="Stage raised an exception",
                        error=str(exc)[:500],
                    )
                )

        return JobSearchPipelineRunResponse(trace_id=trace_id, user_id=user_id, stages=outcomes)

    async def _data_collection(
        self,
        session: AsyncSession,
        settings: Settings,
        user_id: str,
        body: JobSearchPipelineRunRequest,
        trace_id: str,
    ) -> PipelineStageOutcome:
        """Plan + optional catalog refresh; never blocks the whole app if providers are off."""
        plan = await provider_params_from_user_resume(session, user_id)
        readiness = {
            "adzuna_configured": bool((settings.adzuna_app_id or "").strip() and (settings.adzuna_app_key or "").strip()),
            "greenhouse_boards": len(settings.greenhouse_board_tokens_list()),
            "serpapi_configured": bool((settings.serpapi_api_key or "").strip()),
            "scrapling_enabled": bool(settings.scrapling_enabled),
        }
        detail: dict = {
            "readiness": readiness,
            "resume_query_plan": {
                "keywords": plan.keywords if plan else None,
                "location": plan.location if plan else None,
            },
            "trace_id": trace_id,
        }

        if not body.trigger_catalog_refresh:
            return PipelineStageOutcome(
                stage=JobSearchPipelineStageId.data_collection,
                ok=True,
                summary="Data collection plan computed; catalog refresh not requested.",
                detail=detail,
            )

        if not (settings.job_catalog_ingestion_user_id or "").strip():
            return PipelineStageOutcome(
                stage=JobSearchPipelineStageId.data_collection,
                ok=False,
                summary="Cannot refresh catalog: JOB_CATALOG_INGESTION_USER_ID is not set",
                detail=detail,
                error="missing_catalog_actor",
            )

        from services.catalog_ingest_orchestrator import run_catalog_preset_ingest

        try:
            ingest = await run_catalog_preset_ingest(
                session,
                settings,
                preset=body.catalog_preset,
                user_id=user_id,
                keywords=None,
                location=None,
                country=None,
                start_page=1,
                resume_aligned=body.resume_aligned_catalog,
                include_legacy_connectors=body.include_legacy_connectors,
                include_scrapling=body.include_scrapling,
            )
            detail["catalog_ingest"] = {
                "status": ingest.status,
                "created": ingest.created,
                "updated": ingest.updated,
                "providers": [p.model_dump() for p in ingest.providers],
            }
            return PipelineStageOutcome(
                stage=JobSearchPipelineStageId.data_collection,
                ok=ingest.status != "failed",
                summary=f"Catalog ingest finished with status={ingest.status}",
                detail=detail,
            )
        except ValueError as exc:
            return PipelineStageOutcome(
                stage=JobSearchPipelineStageId.data_collection,
                ok=False,
                summary="Catalog ingest could not run",
                detail=detail,
                error=str(exc)[:500],
            )

    async def _resume_profile(self, session: AsyncSession, user_id: str) -> PipelineStageOutcome:
        row = (
            await session.execute(
                select(Resume)
                .where(Resume.user_id == user_id)
                .order_by(Resume.created_at.desc(), Resume.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            return PipelineStageOutcome(
                stage=JobSearchPipelineStageId.resume_profile,
                ok=False,
                summary="No resume on file",
                detail={"has_resume": False},
                error="no_resume",
            )

        parsed = normalize_parsed_profile_dict(row.parsed_profile or {})
        prefs = merge_preferences_dicts(row.preferences, {})
        return PipelineStageOutcome(
            stage=JobSearchPipelineStageId.resume_profile,
            ok=True,
            summary="Resume profile loaded",
            detail={
                "has_resume": True,
                "resume_id": row.id,
                "headline": parsed.get("headline"),
                "skills_top": (parsed.get("top_skills") or parsed.get("skills") or [])[:12],
                "target_role": prefs.get("target_role"),
                "location_pref": prefs.get("location"),
            },
        )

    async def _job_matching(self, session: AsyncSession, user_id: str) -> PipelineStageOutcome:
        n = await recompute_job_scores_for_user(session, user_id)
        return PipelineStageOutcome(
            stage=JobSearchPipelineStageId.job_matching,
            ok=True,
            summary=f"Recomputed job scores for user ({n} rows refreshed)",
            detail={"refreshed_scores": n},
        )

    async def _outbound_application(self, session: AsyncSession, user_id: str) -> PipelineStageOutcome:
        pending = (
            await session.execute(
                select(func.count(Approval.id)).where(Approval.user_id == user_id, Approval.status == "pending")
            )
        ).scalar_one()
        apps = (await session.execute(select(func.count(Application.id)).where(Application.user_id == user_id))).scalar_one()
        return PipelineStageOutcome(
            stage=JobSearchPipelineStageId.outbound_application,
            ok=True,
            summary="Outbound / pipeline snapshot",
            detail={
                "pending_approvals": int(pending or 0),
                "applications_tracked": int(apps or 0),
            },
        )

    async def _feedback(
        self, session: AsyncSession, user_id: str, body: JobSearchPipelineRunRequest, trace_id: str
    ) -> PipelineStageOutcome:
        stmt = (
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        rows = (await session.execute(stmt)).all()
        by_status = {str(status): int(ct) for status, ct in rows}

        row = (
            await session.execute(
                select(Resume)
                .where(Resume.user_id == user_id)
                .order_by(Resume.created_at.desc(), Resume.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        prior = None
        if row and row.preferences:
            fl = (row.preferences or {}).get("feedback_learning")
            if isinstance(fl, dict):
                prior = fl

        snapshot = compute_feedback_snapshot(by_status, trace_id=trace_id, prior_feedback_learning=prior)
        detail: dict = {
            "applications_by_status": by_status,
            "feedback_learning": snapshot,
        }

        if body.persist_feedback_learning:
            persist_detail: dict = {"attempted": True, "ok": False}
            try:
                await persist_feedback_learning_snapshot(session, user_id, snapshot)
                persist_detail["ok"] = True
            except LookupError:
                persist_detail["error"] = "no_resume"
            except Exception:
                logger.exception("persist feedback_learning failed user_id=%s", user_id)
                persist_detail["error"] = "persist_failed"
            detail["persist_feedback_learning"] = persist_detail

        return PipelineStageOutcome(
            stage=JobSearchPipelineStageId.feedback,
            ok=True,
            summary="Application outcomes + advisory feedback snapshot",
            detail=detail,
        )


coordinator = JobSearchPipelineCoordinator()
