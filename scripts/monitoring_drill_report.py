#!/usr/bin/env python3
"""Generate evidence for Week 3 Day 18 monitoring drill readiness.

This script captures a point-in-time operational snapshot and can compute
mean-time-to-detect (MTTD) from incident and alert timestamps.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class EndpointCheck:
    path: str
    status: int
    latency_ms: float
    body_preview: str


def _request(url: str, timeout_s: float = 15.0) -> EndpointCheck:
    start = time.perf_counter()
    req = urllib.request.Request(url=url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return EndpointCheck(path=url, status=int(resp.status), latency_ms=elapsed_ms, body_preview=body[:4000])
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return EndpointCheck(path=url, status=int(exc.code), latency_ms=elapsed_ms, body_preview=body[:4000])
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return EndpointCheck(path=url, status=599, latency_ms=elapsed_ms, body_preview=f"probe_error: {exc}")


def _parse_iso8601(raw: str) -> dt.datetime:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _seconds_between(start_iso: str | None, detected_iso: str | None) -> float | None:
    if not start_iso or not detected_iso:
        return None
    start = _parse_iso8601(start_iso)
    detected = _parse_iso8601(detected_iso)
    return (detected - start).total_seconds()


def _read_ready_json(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _render_report(
    *,
    generated_at: str,
    checks: list[EndpointCheck],
    incident_started_at: str | None,
    alert_detected_at: str | None,
    oncall_owner: str | None,
) -> str:
    lines: list[str] = []
    lines.append("# Day 18 Monitoring Drill Report")
    lines.append("")
    lines.append(f"- Generated at (UTC): `{generated_at}`")
    if oncall_owner:
        lines.append(f"- On-call owner: `{oncall_owner}`")
    if incident_started_at:
        lines.append(f"- Incident started at (UTC): `{incident_started_at}`")
    if alert_detected_at:
        lines.append(f"- Alert detected at (UTC): `{alert_detected_at}`")

    detection_s = _seconds_between(incident_started_at, alert_detected_at)
    if detection_s is not None:
        lines.append(f"- Detection latency: `{detection_s:.1f}s`")
        if detection_s <= 600:
            lines.append("- Drill threshold: `PASS` (<= 10 minutes)")
        else:
            lines.append("- Drill threshold: `FAIL` (> 10 minutes)")
    else:
        lines.append("- Detection latency: `N/A` (set both --incident-started-at and --alert-detected-at)")
    lines.append("")

    lines.append("## Endpoint Snapshot")
    lines.append("")
    lines.append("| Endpoint | Status | Latency (ms) | Key notes |")
    lines.append("|---|---:|---:|---|")
    for check in checks:
        notes = ""
        if check.path.endswith("/ready"):
            ready = _read_ready_json(check.body_preview)
            if ready:
                status_txt = ready.get("status")
                postgres = ready.get("postgres")
                redis = ready.get("redis")
                durability = ready.get("background_durability")
                notes = f"status={status_txt}; postgres={postgres}; redis={redis}; background_durability={durability}"
            else:
                notes = "non-json response"
        elif check.path.endswith("/metrics"):
            notes = "metrics scrape surface reachable" if check.status == 200 else "metrics unavailable"
        else:
            notes = "liveness check"
        lines.append(f"| `{check.path}` | `{check.status}` | `{check.latency_ms:.1f}` | {notes} |")

    lines.append("")
    lines.append("## Evidence Links To Add")
    lines.append("")
    lines.append("- Alert notification screenshot/link (Slack/PagerDuty thread)")
    lines.append("- Dashboard screenshot for 5xx/auth/readiness panel around drill window")
    lines.append("- Incident channel summary with owner + timeline")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Day 18 monitoring drill report.")
    parser.add_argument("--base-url", required=True, help="API base URL, e.g. https://doubow-production.up.railway.app")
    parser.add_argument("--incident-started-at", default=None, help="UTC ISO8601 time when drill incident started")
    parser.add_argument("--alert-detected-at", default=None, help="UTC ISO8601 time when first alert was observed")
    parser.add_argument("--oncall-owner", default=None, help="On-call owner name or handle")
    parser.add_argument(
        "--output",
        default="docs/operations/evidence/day18-monitoring-drill.md",
        help="Where to write the markdown report",
    )
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    endpoints = [f"{base}/healthz", f"{base}/ready", f"{base}/metrics"]
    checks = [_request(url) for url in endpoints]

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    report = _render_report(
        generated_at=generated_at,
        checks=checks,
        incident_started_at=args.incident_started_at,
        alert_detected_at=args.alert_detected_at,
        oncall_owner=args.oncall_owner,
    )
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(report)
    print(f"Wrote report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
