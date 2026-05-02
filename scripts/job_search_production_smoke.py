#!/usr/bin/env python3
"""
HTTP smoke checks against a deployed Doubow API (staging or production).

Usage:

  export DOUBOW_API_BASE="https://your-api.example.com"
  export DOUBOW_API_TOKEN="<Clerk JWT>"
  python3 scripts/job_search_production_smoke.py

Optional:

  --production-contract   Require GET/DELETE /v1/me/preferences/feedback-learning → 404
                            (use for production; disable for staging where env != production)

Exit codes: 0 = all checks passed, 1 = failure, 2 = misconfiguration.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any


def _request(
    method: str,
    base: str,
    path: str,
    token: str | None,
    *,
    accept: str | None = None,
) -> tuple[int, bytes]:
    url = base.rstrip("/") + path
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, method=method, headers=headers)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Job-search pipeline production smoke checks.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("DOUBOW_API_BASE", "").strip(),
        help="API origin (or set DOUBOW_API_BASE)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("DOUBOW_API_TOKEN", "").strip(),
        help="Clerk Bearer JWT (or set DOUBOW_API_TOKEN)",
    )
    env_prod = os.environ.get("DOUBOW_PRODUCTION_CONTRACT", "").lower() in ("1", "true", "yes")
    parser.add_argument(
        "--production-contract",
        action="store_true",
        default=env_prod,
        help="Expect feedback-learning debug routes to return 404 (set DOUBOW_PRODUCTION_CONTRACT=1 or pass this flag)",
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        help="Do not require feedback-learning routes to 404 (for non-production env)",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip GET /healthz",
    )
    args = parser.parse_args()

    base = args.base_url
    token = args.token
    if not base:
        print("DOUBOW_API_BASE or --base-url is required", file=sys.stderr)
        return 2
    if not token:
        print("DOUBOW_API_TOKEN or --token is required for authenticated checks", file=sys.stderr)
        return 2

    failures: list[str] = []

    if not args.skip_health:
        code, _ = _request("GET", base, "/healthz", None)
        if code != 200:
            failures.append(f"GET /healthz expected 200, got {code}")

    code, body = _request("GET", base, "/v1/agents/capabilities", token)
    if code != 200:
        failures.append(f"GET /v1/agents/capabilities expected 200, got {code}")
    else:
        try:
            data = json.loads(body.decode())
            tools = data.get("tools") or []
            names = [t.get("name") for t in tools if isinstance(t, dict)]
            if "run_job_search_pipeline" not in names:
                failures.append("capabilities.tools missing run_job_search_pipeline")
        except json.JSONDecodeError:
            failures.append("capabilities response is not JSON")

    production_contract = args.production_contract and not args.staging
    if production_contract:
        for method, path in (("GET", "/v1/me/preferences/feedback-learning"), ("DELETE", "/v1/me/preferences/feedback-learning")):
            code, _ = _request(method, base, path, token)
            if code != 404:
                failures.append(f"{method} {path} expected 404 in production contract, got {code}")

    code, body = _request("GET", base, "/metrics", None)
    if code != 200:
        failures.append(f"GET /metrics expected 200, got {code}")
    else:
        text = body.decode("utf-8", errors="replace")
        if "doubow_matching_blend_score_sync_total" not in text:
            failures.append("GET /metrics missing doubow_matching_blend_score_sync_total")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1

    print("OK: job-search production smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
