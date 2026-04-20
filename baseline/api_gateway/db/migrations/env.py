from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from db.dotenv_merge import load_dotenv_merged
from db.session import Base
from db.url_utils import normalize_db_url
import models  # noqa: F401


load_dotenv_merged(Path(__file__).resolve().parent)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def resolve_database_url() -> str:
    # Order: explicit migrate URL first. For Supabase, `db.*.supabase.co` (direct) is often IPv6-only;
    # use Session pooler :5432 (e.g. ALEMBIC_DATABASE_URL) on IPv4-only networks — see Supabase “Connect”.
    candidates = [
        os.getenv("ALEMBIC_DATABASE_URL"),
        os.getenv("DATABASE_URL"),
        os.getenv("POOLER_SESSION_DATABASE_URL"),
        os.getenv("NEXT_PUBLIC_POOLER_SESSION_URL"),
        os.getenv("NEXT_PUBLIC_DIRECT_URL"),
        os.getenv("NEXT_PUBLIC_DATABASE_URL"),
    ]
    for candidate in candidates:
        if candidate:
            url = normalize_db_url(candidate)
            # Alembic uses a synchronous engine; strip async drivers from the same DATABASE_URL as the app.
            if url.startswith("postgresql+asyncpg://"):
                url = "postgresql://" + url.removeprefix("postgresql+asyncpg://")
            elif url.startswith("postgres+asyncpg://"):
                url = "postgresql://" + url.removeprefix("postgres+asyncpg://")
            return url
    raise RuntimeError("No database URL found in DATABASE_URL/NEXT_PUBLIC_DIRECT_URL/NEXT_PUBLIC_DATABASE_URL")


def run_migrations_offline() -> None:
    url = resolve_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg_section = config.get_section(config.config_ini_section, {})
    cfg_section["sqlalchemy.url"] = resolve_database_url()
    connectable = engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
