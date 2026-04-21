#!/usr/bin/env python3
"""Print Week 1 baseline KPIs from current DB/telemetry.

Usage:
  python scripts/baseline_report.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

try:
    from sqlalchemy import func, select
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "Missing dependency: sqlalchemy. Run with a backend virtualenv, for example:\n"
        "  ./.venv-test/bin/python scripts/baseline_report.py"
    ) from exc


def _bootstrap_api_gateway_imports() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    api_gateway_dir = repo_root / "backend" / "api_gateway"
    sys.path.insert(0, str(api_gateway_dir))


_bootstrap_api_gateway_imports()

from db.session import SessionLocal  # noqa: E402
from models.approval import Approval  # noqa: E402
from models.job_score import JobScore  # noqa: E402
from models.telemetry_event import TelemetryEvent  # noqa: E402


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _fetch_baseline() -> dict[str, str]:
    async with SessionLocal() as session:
        # 1-2) Activation speed from telemetry event properties.
        rows = await session.execute(
            select(TelemetryEvent.properties).where(TelemetryEvent.event_name == "first_matches_ready")
        )
        ttfm_values: list[float] = []
        for props in rows.scalars():
            if not isinstance(props, dict):
                continue
            seconds = _as_float(props.get("time_to_first_matches_seconds"))
            if seconds is not None and seconds >= 0:
                ttfm_values.append(seconds)

        ttfm_avg = sum(ttfm_values) / len(ttfm_values) if ttfm_values else None
        ttfm_latest = ttfm_values[-1] if ttfm_values else None

        # 3) Match quality proxy: high-fit share.
        total_scores = (
            await session.execute(select(func.count()).select_from(JobScore))
        ).scalar_one()
        high_fit_scores = (
            await session.execute(select(func.count()).select_from(JobScore).where(JobScore.fit_score >= 4.0))
        ).scalar_one()
        high_fit_ratio = (high_fit_scores / total_scores) if total_scores else None

        # 4) Approval conversion: sent / created.
        approvals_created = (
            await session.execute(select(func.count()).select_from(Approval))
        ).scalar_one()
        approvals_sent = (
            await session.execute(
                select(func.count())
                .select_from(Approval)
                .where((Approval.sent_at.is_not(None)) | (Approval.status.in_(("sent", "approved_and_sent"))))
            )
        ).scalar_one()
        approvals_conversion = (approvals_sent / approvals_created) if approvals_created else None

        # 5) Reliability proxy: api_error* / api_* events when available.
        api_events_total = (
            await session.execute(
                select(func.count()).select_from(TelemetryEvent).where(TelemetryEvent.event_name.like("api_%"))
            )
        ).scalar_one()
        api_error_events = (
            await session.execute(
                select(func.count()).select_from(TelemetryEvent).where(TelemetryEvent.event_name.like("api_error%"))
            )
        ).scalar_one()
        api_error_rate = (api_error_events / api_events_total) if api_events_total else None

        return {
            "activation_ttfm_avg_seconds": f"{ttfm_avg:.1f}" if ttfm_avg is not None else "n/a",
            "activation_ttfm_latest_seconds": f"{ttfm_latest:.1f}" if ttfm_latest is not None else "n/a",
            "match_quality_high_fit_ratio": f"{high_fit_ratio:.2%}" if high_fit_ratio is not None else "n/a",
            "approval_conversion_sent_over_created": (
                f"{approvals_conversion:.2%}" if approvals_conversion is not None else "n/a"
            ),
            "reliability_api_error_rate": (
                f"{api_error_rate:.2%}" if api_error_rate is not None else "n/a (no api_* telemetry events)"
            ),
        }


async def _main() -> int:
    try:
        report = await _fetch_baseline()
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        print("Doubow Week 1 Baseline KPI Report")
        print("---------------------------------")
        print(f"error: unable to query database/telemetry ({exc.__class__.__name__})")
        print("hint: start backend Postgres stack and ensure DATABASE_URL is reachable.")
        return 1
    print("Doubow Week 1 Baseline KPI Report")
    print("---------------------------------")
    for key, value in report.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
