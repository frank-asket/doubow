"""Map ``AutopilotRun`` rows to API responses."""

from models.autopilot_run import AutopilotRun
from schemas.autopilot import AutopilotRunItem, AutopilotRunResponse


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
        scope=run.scope,  # type: ignore[arg-type]
        item_results=items,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )
