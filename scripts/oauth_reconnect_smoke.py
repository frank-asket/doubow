#!/usr/bin/env python3
"""Smoke-check OAuth reconnect API preflight for Step 7.

Checks authenticated OAuth endpoints for Google and LinkedIn:
- GET /v1/integrations/{provider}/status
- GET /v1/integrations/{provider}/authorize

PASS criteria (point-in-time):
- No 5xx/network failures
- /authorize returns JSON with non-empty authorization_url
- No obvious misconfiguration detail messages

Optional diagnostics mode:
- On failure, call /v1/me/debug/oauth-config and print missing required keys.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass
class CheckResult:
    provider: str
    endpoint: str
    status: int
    ok: bool
    note: str = ""


def _extract_http_error_detail(raw: str) -> str | None:
    if not raw.strip():
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return raw[:240]
    if isinstance(parsed, dict):
        detail = parsed.get("detail")
        if isinstance(detail, str):
            return detail
        message = parsed.get("message")
        if isinstance(message, str):
            return message
    return None


def _request_json(
    *,
    base_url: str,
    token: str,
    path: str,
    timeout_s: float = 20.0,
) -> tuple[int, dict[str, Any] | None, str | None]:
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(
        url=url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload: dict[str, Any] | None = None
            if raw.strip():
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        payload = parsed
                except Exception:
                    payload = None
            return int(resp.status), payload, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail = _extract_http_error_detail(raw)
        return int(exc.code), None, detail
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        return 599, None, f"network_error: {reason}"
    except (socket.timeout, TimeoutError) as exc:
        return 599, None, f"network_timeout: {exc}"
    except Exception as exc:
        return 599, None, f"probe_exception: {type(exc).__name__}: {exc}"


def _is_valid_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
    except Exception:
        return False
    return bool(parsed.scheme in {"http", "https"} and parsed.netloc)


def _status_check(provider: str, status: int, payload: dict[str, Any] | None, detail: str | None) -> CheckResult:
    endpoint = "status"
    if status >= 500:
        return CheckResult(provider, endpoint, status, False, detail or "server/network failure")
    if status < 200 or status >= 300:
        return CheckResult(provider, endpoint, status, False, detail or "unexpected non-2xx response")
    if payload is None:
        return CheckResult(provider, endpoint, status, False, "invalid/missing JSON body")
    connected = payload.get("connected")
    if not isinstance(connected, bool):
        return CheckResult(provider, endpoint, status, False, "missing boolean 'connected' in payload")
    note = f"connected={connected}"
    if provider == "google":
        ge = payload.get("google_email")
        if ge is not None and not isinstance(ge, str):
            return CheckResult(provider, endpoint, status, False, "invalid 'google_email' shape")
    if provider == "linkedin":
        expires = payload.get("expires_at")
        if expires is not None and not isinstance(expires, str):
            return CheckResult(provider, endpoint, status, False, "invalid 'expires_at' shape")
    return CheckResult(provider, endpoint, status, True, note)


def _authorize_check(provider: str, status: int, payload: dict[str, Any] | None, detail: str | None) -> CheckResult:
    endpoint = "authorize"
    if status >= 500:
        return CheckResult(provider, endpoint, status, False, detail or "server/network failure")
    if status < 200 or status >= 300:
        return CheckResult(provider, endpoint, status, False, detail or "unexpected non-2xx response")
    if payload is None:
        return CheckResult(provider, endpoint, status, False, "invalid/missing JSON body")
    auth_url = payload.get("authorization_url")
    if not isinstance(auth_url, str) or not auth_url.strip():
        return CheckResult(provider, endpoint, status, False, "missing 'authorization_url'")
    if not _is_valid_url(auth_url):
        return CheckResult(provider, endpoint, status, False, "authorization_url is not a valid http(s) URL")
    return CheckResult(provider, endpoint, status, True, "authorization_url ok")


def _print_oauth_diagnostics(*, base_url: str, token: str, failed: list[CheckResult]) -> None:
    has_linkedin_authorize_failure = any(
        r.provider == "linkedin" and r.endpoint == "authorize" and not r.ok for r in failed
    )
    if not has_linkedin_authorize_failure:
        return

    status, payload, detail = _request_json(base_url=base_url, token=token, path="/v1/me/debug/oauth-config")
    print("\n== Diagnostic mode ==")
    if status != 200 or payload is None:
        print(
            "diagnostic endpoint unavailable:"
            f" code={status} reason={detail or 'unknown'}"
        )
        return

    linkedin = payload.get("linkedin")
    if not isinstance(linkedin, dict):
        print("diagnostic payload missing linkedin config section")
        return

    missing = linkedin.get("missing_required_keys")
    configured = linkedin.get("configured")
    if not isinstance(missing, list):
        print("diagnostic payload missing linkedin.missing_required_keys")
        return

    if missing:
        joined = ", ".join(str(x) for x in missing)
        print(f"linkedin configured={configured} missing_required_keys=[{joined}]")
    else:
        print(
            "linkedin configured appears complete in debug endpoint."
            " Re-check provider console redirect URI/client credentials."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="OAuth reconnect preflight smoke check for Step 7.")
    parser.add_argument("--base-url", required=True, help="API base URL, e.g. https://doubow-production.up.railway.app")
    parser.add_argument("--token", default=None, help="Clerk bearer token for an end-user account")
    parser.add_argument(
        "--token-env",
        default="DOUBOW_LAUNCH_PROBE_TOKEN",
        help="Env var to read bearer token from when --token is omitted",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="On failure, call /v1/me/debug/oauth-config and print missing key diagnostics",
    )
    args = parser.parse_args()

    token = args.token or os.getenv(args.token_env)
    if not token:
        print(f"FAIL: missing bearer token. Pass --token or set {args.token_env}.")
        return 2

    providers = ("google", "linkedin")
    results: list[CheckResult] = []

    print("== OAuth reconnect smoke ==")
    print(f"base_url={args.base_url}")
    print("")

    for provider in providers:
        status_path = f"/v1/integrations/{provider}/status"
        authz_path = f"/v1/integrations/{provider}/authorize"

        status_code, status_payload, status_detail = _request_json(
            base_url=args.base_url, token=token, path=status_path
        )
        r1 = _status_check(provider, status_code, status_payload, status_detail)
        results.append(r1)
        print(
            f"{provider:<8} status     code={r1.status:<3} {'OK' if r1.ok else 'FAIL'}"
            f"{f'  ({r1.note})' if r1.note else ''}"
        )

        authz_code, authz_payload, authz_detail = _request_json(
            base_url=args.base_url, token=token, path=authz_path
        )
        r2 = _authorize_check(provider, authz_code, authz_payload, authz_detail)
        results.append(r2)
        print(
            f"{provider:<8} authorize  code={r2.status:<3} {'OK' if r2.ok else 'FAIL'}"
            f"{f'  ({r2.note})' if r2.note else ''}"
        )

    failed = [r for r in results if not r.ok]
    print("\n== Step 7 preflight result ==")
    if not failed:
        print("PASS: OAuth API preflight checks succeeded for Google and LinkedIn.")
        return 0

    print("FAIL: One or more OAuth preflight checks failed:")
    for r in failed:
        print(f"- {r.provider}.{r.endpoint}: code={r.status} reason={r.note or 'unknown'}")
    if args.diagnose:
        _print_oauth_diagnostics(base_url=args.base_url, token=token, failed=failed)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

