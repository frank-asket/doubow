#!/usr/bin/env python3
"""Probe P0-2 auth/session health for DouBow production.

Checks authenticated endpoints for auth-specific failure patterns and summarizes
whether the auth gate is healthy enough to continue launch-readiness work.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EndpointStats:
    name: str
    method: str
    path: str
    statuses: list[int] = field(default_factory=list)
    auth_errors: list[str] = field(default_factory=list)
    server_errors: int = 0

    def record(self, status: int, detail: str | None) -> None:
        self.statuses.append(status)
        if status >= 500:
            self.server_errors += 1
        if detail:
            d = detail.lower()
            if "auth" in d or "authorization" in d or "issuer" in d or "token" in d or "provider" in d:
                self.auth_errors.append(detail)


def _req(
    *,
    base_url: str,
    token: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    timeout_s: float = 20.0,
) -> tuple[int, str]:
    url = f"{base_url.rstrip('/')}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url=url, headers=headers, data=payload, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return int(resp.status), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return int(exc.code), raw


def _extract_detail(raw: str) -> str | None:
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return raw[:300]
    if isinstance(data, dict):
        if isinstance(data.get("detail"), str):
            return data["detail"]
        err = data.get("error")
        if isinstance(err, dict):
            msg = err.get("message")
            if isinstance(msg, str):
                return msg
        if isinstance(data.get("message"), str):
            return data["message"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe auth/session health for launch gate P0-2.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", default=None)
    parser.add_argument("--token-env", default="DOUBOW_LAUNCH_PROBE_TOKEN")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    args = parser.parse_args()

    token = args.token or os.getenv(args.token_env)
    if not token:
        print(f"ERROR: missing token. Use --token or set {args.token_env}.")
        return 2

    endpoints: list[tuple[EndpointStats, dict[str, Any] | None]] = [
        (EndpointStats("me_debug", "GET", "/v1/me/debug"), None),
        (EndpointStats("applications", "GET", "/v1/me/applications"), None),
        (EndpointStats("approvals", "GET", "/v1/me/approvals"), None),
        (
            EndpointStats("agents_chat", "POST", "/v1/agents/chat"),
            {"message": "Auth health probe. Reply with one short line.", "thread_id": None},
        ),
    ]

    print(f"== Auth gate probe ==\nbase_url={args.base_url}\niterations={args.iterations}\n")
    for i in range(args.iterations):
        print(f"[sample {i + 1}/{args.iterations}]")
        for ep, body in endpoints:
            status, raw = _req(
                base_url=args.base_url,
                token=token,
                method=ep.method,
                path=ep.path,
                body=body,
            )
            detail = _extract_detail(raw)
            ep.record(status, detail)
            tag = f"detail={detail}" if detail else ""
            print(f"  {ep.name:<12} status={status:<3} {tag}")
            time.sleep(max(0.0, args.sleep_seconds))

    print("\n== Summary ==")
    go = True
    for ep, _ in endpoints:
        total = len(ep.statuses)
        five_xx = ep.server_errors
        print(f"{ep.name:<12} samples={total:<3} 5xx={five_xx:<3} auth_signals={len(ep.auth_errors)}")
        if five_xx > 0:
            go = False
            print("  - FAIL: server errors observed on authenticated path")
        for msg in ep.auth_errors[:3]:
            print(f"  - auth signal: {msg}")

    if go:
        print("\nDecision: PASS (point-in-time) — no auth-path 5xx detected.")
        return 0
    print("\nDecision: FAIL (point-in-time) — investigate auth/session path before launch.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
