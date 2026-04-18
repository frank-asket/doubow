from __future__ import annotations

import os
from logging.config import fileConfig
from urllib.parse import quote, unquote

from alembic import context
from sqlalchemy import engine_from_config, pool

from db.session import Base
import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def normalize_db_url(url: str) -> str:
    """
    Normalize DATABASE_URL-like values and URL-encode unsafe passwords.
    Handles inputs such as:
      postgresql://user:pa?ss@host:5432/db
    """
    if "://" not in url or ":" not in url or "@" not in url:
        return url

    scheme, rest = url.split("://", 1)
    if "/" not in rest:
        return url

    userinfo_host, path_q = rest.split("/", 1)
    if ":" not in userinfo_host or "@" not in userinfo_host:
        return url

    user, pass_host = userinfo_host.split(":", 1)
    password, host = pass_host.rsplit("@", 1)
    encoded_password = quote(unquote(password), safe="")
    return f"{scheme}://{user}:{encoded_password}@{host}/{path_q}"


def resolve_database_url() -> str:
    candidates = [
        os.getenv("ALEMBIC_DATABASE_URL"),
        os.getenv("DATABASE_URL"),
        os.getenv("NEXT_PUBLIC_DIRECT_URL"),
        os.getenv("NEXT_PUBLIC_DATABASE_URL"),
    ]
    for candidate in candidates:
        if candidate:
            return normalize_db_url(candidate)
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
