#!/usr/bin/env python3
"""Probe DouBow production launch gates (P0-1 + P1-4 baseline checks).

Usage:
  python3 scripts/launch_gate_probe.py \
    --base-url https://doubow-production.up.railway.app \
    --token "<clerk_jwt>" \
    --iterations 20 \
    --sleep-seconds 2.0

Notes:
- This is a point-in-time probe, not a replacement for 48-72h observability windows.
- It targets the four critical authenticated routes from launch-go-no-go-checklist.md.
"""

from __future__ import annotations

import argparse
import os
import json
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RouteResult:
    name: str
    method: str
    path: str
    statuses: list[int] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def record(self, status: int, latency_ms: float) -> None:
        self.statuses.append(status)
        self.latencies_ms.append(latency_ms)

    @property
    def count(self) -> int:
        return len(self.statuses)

    @property
    def p95_ms(self) -> float | None:
        if not self.latencies_ms:
            return None
        vals = sorted(self.latencies_ms)
        idx = max(0, min(len(vals) - 1, int(round(0.95 * (len(vals) - 1)))))
        return vals[idx]

    @property
    def mean_ms(self) -> float | None:
        if not self.latencies_ms:
            return None
        return statistics.mean(self.latencies_ms)

    @property
    def five_xx_rate(self) -> float:
        if not self.statuses:
            return 1.0
        failures = sum(1 for s in self.statuses if s >= 500)
        return failures / len(self.statuses)


def _request_once(
    *,
    base_url: str,
    token: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    timeout_s: float = 20.0,
) -> tuple[int, float]:
    url = f"{base_url.rstrip('/')}{path}"
    payload = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=payload, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return int(resp.status), elapsed_ms
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return int(exc.code), elapsed_ms


def evaluate_gate_thresholds(route: RouteResult) -> list[str]:
    notes: list[str] = []
    if route.five_xx_rate > 0.005:
        notes.append(f"5xx rate {route.five_xx_rate * 100:.2f}% exceeds 0.5%")

    p95 = route.p95_ms
    if p95 is None:
        notes.append("no latency samples")
        return notes

    p95_thresholds = {
        "jobs": 1500.0,
        "applications": 1000.0,
        "approvals": 1000.0,
        "agents_chat": 15000.0,
    }
    th = p95_thresholds.get(route.name)
    if th is not None and p95 > th:
        notes.append(f"P95 {p95:.1f}ms exceeds {th:.0f}ms")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe launch gate routes in production.")
    parser.add_argument("--base-url", required=True, help="API base URL, e.g. https://doubow-production.up.railway.app")
    parser.add_argument("--token", default=None, help="Clerk bearer token for an end-user account")
    parser.add_argument(
        "--token-env",
        default="DOUBOW_LAUNCH_PROBE_TOKEN",
        help="Env var to read bearer token from when --token is omitted",
    )
    parser.add_argument("--iterations", type=int, default=10, help="Number of samples per route")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Delay between calls")
    args = parser.parse_args()
    token = args.token or os.getenv(args.token_env)
    if not token:
        print(
            f"ERROR: missing bearer token. Pass --token or set {args.token_env}.",
        )
        return 2

    routes: list[tuple[RouteResult, dict[str, Any] | None]] = [
        (RouteResult(name="jobs", method="GET", path="/v1/jobs?"), None),
        (RouteResult(name="applications", method="GET", path="/v1/me/applications"), None),
        (RouteResult(name="approvals", method="GET", path="/v1/me/approvals"), None),
        (
            RouteResult(name="agents_chat", method="POST", path="/v1/agents/chat"),
            {"message": "Health check: reply with one short line.", "thread_id": None},
        ),
    ]

    print(f"== Launch gate probe ==\nbase_url={args.base_url}\niterations={args.iterations}\n")
    for i in range(args.iterations):
        print(f"[sample {i + 1}/{args.iterations}]")
        for route, body in routes:
            try:
                status, latency = _request_once(
                    base_url=args.base_url,
                    token=token,
                    method=route.method,
                    path=route.path,
                    body=body,
                )
                route.record(status, latency)
                print(f"  {route.name:<13} status={status:<3} latency_ms={latency:.1f}")
            except Exception as exc:  # noqa: BLE001
                route.errors.append(str(exc))
                print(f"  {route.name:<13} ERROR {exc}")
            time.sleep(max(0.0, args.sleep_seconds))

    print("\n== Summary ==")
    combined_statuses = [s for r, _ in routes for s in r.statuses]
    combined_5xx = sum(1 for s in combined_statuses if s >= 500) / max(1, len(combined_statuses))

    go = True
    for route, _ in routes:
        notes = evaluate_gate_thresholds(route)
        status_line = (
            f"{route.name:<13} samples={route.count:<3} "
            f"5xx_rate={route.five_xx_rate * 100:>6.2f}% "
            f"p95_ms={(route.p95_ms or 0):>8.1f} "
            f"mean_ms={(route.mean_ms or 0):>8.1f}"
        )
        print(status_line)
        if notes:
            go = False
            for n in notes:
                print(f"  - FAIL: {n}")
        if route.errors:
            go = False
            print(f"  - FAIL: runtime errors ({len(route.errors)})")

    print(f"\ncombined_5xx_rate={combined_5xx * 100:.2f}% (threshold 0.25%)")
    if combined_5xx > 0.0025:
        print("  - FAIL: combined 5xx exceeds P0-1 threshold")
        go = False

    print("\nDecision (point-in-time probe only):")
    print("  GO" if go else "  NO-GO")
    return 0 if go else 2


if __name__ == "__main__":
    raise SystemExit(main())
