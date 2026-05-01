#!/usr/bin/env python3
"""Print DATABASE_URL normalized for psycopg2 and libpq/psql.

Strips SQLAlchemy async driver prefixes (postgresql+asyncpg) and rewrites
query param ``ssl=`` to ``sslmode=`` (asyncpg/ssl accepted; psycopg2/psql are not).
"""
from __future__ import annotations

import os
import sys
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize(raw: str) -> str:
    raw = raw.strip()
    u = urlparse(raw)
    scheme = (
        u.scheme.replace("postgresql+asyncpg", "postgresql").replace("postgres+asyncpg", "postgresql")
    )
    params: list[tuple[str, str]] = []
    for k, v in parse_qsl(u.query, keep_blank_values=True):
        if k == "ssl":
            mode = "require" if (v or "").lower() in {"1", "true", "yes", "require"} else "disable"
            params.append(("sslmode", mode))
        else:
            params.append((k, v))
    return urlunparse((scheme, u.netloc, u.path, u.params, urlencode(params), u.fragment))


def main() -> None:
    db = os.environ.get("DATABASE_URL", "").strip()
    if not db:
        print("DATABASE_URL is required", file=sys.stderr)
        sys.exit(1)
    print(normalize(db))


if __name__ == "__main__":
    main()
