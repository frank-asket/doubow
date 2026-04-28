from fastapi import HTTPException

from config import settings
from models.user import User
from routers.ingestion import _require_ingestion_admin


def test_ingestion_admin_allows_non_prod_without_allow_list(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "admin_ingestion_user_ids", None)
    user = User(id="user_any", email="any@example.com")
    _require_ingestion_admin(user)


def test_ingestion_admin_requires_allow_list_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "admin_ingestion_user_ids", "user_admin")
    user = User(id="user_non_admin", email="nonadmin@example.com")
    try:
        _require_ingestion_admin(user)
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 403


def test_ingestion_admin_allows_listed_user_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "admin_ingestion_user_ids", "user_admin,user_other")
    user = User(id="user_admin", email="admin@example.com")
    _require_ingestion_admin(user)

