"""Map ``AutopilotRun`` rows to API responses."""

from datetime import datetime, timezone

from config import settings
from models.autopilot_run import AutopilotRun
from schemas.autopilot import AutopilotRunItem, AutopilotRunResponse


def _run_is_resumable(run: AutopilotRun) -> bool:
    if run.status != "running":
        return False
    if settings.use_langgraph_autopilot and settings.use_langgraph_autopilot_checkpoint:
        return bool(run.graph_checkpoint)
    return True


def autopilot_run_to_response(run: AutopilotRun, *, replayed: bool = False) -> AutopilotRunResponse:
    items: list[AutopilotRunItem] | None = None
    raw = run.item_results
    if isinstance(raw, list) and raw:
        parsed: list[AutopilotRunItem] = []
        for x in raw:
            if isinstance(x, dict):
                try:
                    parsed.append(AutopilotRunItem.model_validate(x))
                except Exception:
                    continue
        items = parsed or None
    return AutopilotRunResponse(
        run_id=run.id,
        status=run.status,  # type: ignore[arg-type]
        replayed=replayed,
        replayed_at=datetime.now(timezone.utc) if replayed else None,
        fresh_run=not replayed,
        scope=run.scope,  # type: ignore[arg-type]
        item_results=items,
        failure_code=run.failure_code,
        failure_detail=run.failure_detail,
        failure_node=run.failure_node,
        resumable=_run_is_resumable(run),
        started_at=run.started_at,
        completed_at=run.completed_at,
    )
