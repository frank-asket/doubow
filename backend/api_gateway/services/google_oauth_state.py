"""Signed OAuth `state` for Google callback (no Clerk header on redirect)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def sign_oauth_state(*, user_id: str, secret: str, ttl_seconds: int = 900) -> str:
    """Return `body_b64.signature_hex` — body is JSON {uid, exp}."""
    if not secret:
        raise ValueError("state secret is empty")
    now = int(time.time())
    payload = json.dumps({"uid": user_id, "exp": now + ttl_seconds}, separators=(",", ":"), sort_keys=True)
    body = payload.encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"{_b64url_encode(body)}.{sig}"


def verify_oauth_state(*, token: str, secret: str) -> str:
    """Validate HMAC and expiry; return user id."""
    if not secret:
        raise ValueError("state secret is empty")
    if "." not in token:
        raise ValueError("invalid state format")
    body_b64, sig = token.rsplit(".", 1)
    body = _b64url_decode(body_b64)
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise ValueError("invalid state signature")
    data = json.loads(body.decode("utf-8"))
    uid = data.get("uid")
    exp = data.get("exp")
    if not isinstance(uid, str) or not uid:
        raise ValueError("invalid state payload")
    if not isinstance(exp, int):
        raise ValueError("invalid state expiry")
    now = int(time.time())
    if now > exp:
        raise ValueError("state expired")
    return uid
