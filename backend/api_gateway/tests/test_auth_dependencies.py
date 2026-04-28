from fastapi import HTTPException
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError
import pytest

import dependencies


def test_get_current_user_claims_maps_jwks_client_error_to_401(monkeypatch):
    def _raise(_token: str) -> dict:
        raise PyJWKClientError("Unable to find a signing key")

    monkeypatch.setattr(dependencies, "_decode_clerk_token", _raise)

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user_claims(authorization="Bearer token")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid auth token"


def test_get_current_user_claims_maps_jwks_connection_error_to_503(monkeypatch):
    def _raise(_token: str) -> dict:
        raise PyJWKClientConnectionError("network down")

    monkeypatch.setattr(dependencies, "_decode_clerk_token", _raise)

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user_claims(authorization="Bearer token")

    assert exc.value.status_code == 503
    assert exc.value.detail == "Authentication provider temporarily unavailable"


def test_get_current_user_claims_maps_jwks_http_4xx_to_401(monkeypatch):
    def _raise(_token: str) -> dict:
        raise PyJWKClientConnectionError('Fail to fetch data from the url, err: "HTTP Error 400: Bad Request"')

    monkeypatch.setattr(dependencies, "_decode_clerk_token", _raise)

    with pytest.raises(HTTPException) as exc:
        dependencies.get_current_user_claims(authorization="Bearer token")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid auth token"
