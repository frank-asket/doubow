"""
Optional integration check against a live Postgres URL.

Set CI_POSTGRES_URL (sync DSN, e.g. postgresql://user:pass@host:5432/db) after migrations.
CI sets this alongside online `alembic upgrade head` so the schema matches current heads.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.skipif(not os.getenv("CI_POSTGRES_URL"), reason="CI_POSTGRES_URL not set")
def test_migrated_schema_has_jobs_score_template() -> None:
    url = os.environ["CI_POSTGRES_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        n = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'jobs'
                  AND column_name = 'score_template'
                """
            )
        ).scalar_one()
        assert int(n) == 1

        ver = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert isinstance(ver, str) and len(ver) >= 8

        pol = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM pg_policies
                WHERE tablename = 'users' AND policyname = 'doubow_users_tenant'
                """
            )
        ).scalar_one()
        assert int(pol) >= 1


@pytest.mark.skipif(not os.getenv("CI_POSTGRES_URL"), reason="CI_POSTGRES_URL not set")
def test_migrated_schema_has_linkedin_oauth_contract() -> None:
    url = os.environ["CI_POSTGRES_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        table_exists = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'linkedin_oauth_credentials'
                """
            )
        ).scalar_one()
        assert int(table_exists) == 1

        required_cols = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'linkedin_oauth_credentials'
                  AND column_name IN (
                      'user_id',
                      'access_token_encrypted',
                      'linkedin_member_id',
                      'expires_at',
                      'created_at',
                      'updated_at'
                  )
                """
            )
        ).scalar_one()
        assert int(required_cols) == 6

        idx = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = 'linkedin_oauth_credentials'
                  AND indexname = 'ix_linkedin_oauth_credentials_linkedin_member_id'
                """
            )
        ).scalar_one()
        assert int(idx) >= 1

        rls_enabled = conn.execute(
            text(
                """
                SELECT c.relrowsecurity
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = 'linkedin_oauth_credentials'
                """
            )
        ).scalar_one()
        assert bool(rls_enabled) is True

        policy = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM pg_policies
                WHERE tablename = 'linkedin_oauth_credentials'
                  AND policyname = 'doubow_linkedin_oauth_credentials_tenant'
                """
            )
        ).scalar_one()
        assert int(policy) >= 1
