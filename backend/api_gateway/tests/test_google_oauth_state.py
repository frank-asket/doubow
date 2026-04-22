"""OAuth state signing (Google callback CSRF binding)."""

import pytest

from services.google_oauth_state import sign_oauth_state, verify_oauth_state


def test_sign_verify_roundtrip():
    secret = "test-secret-key-long-enough-for-hmac"
    uid = "user_abc123"
    tok = sign_oauth_state(user_id=uid, secret=secret)
    assert verify_oauth_state(token=tok, secret=secret) == uid


def test_verify_wrong_secret():
    tok = sign_oauth_state(user_id="u1", secret="secret-a")
    with pytest.raises(ValueError):
        verify_oauth_state(token=tok, secret="secret-b")
