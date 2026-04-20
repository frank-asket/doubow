#!/usr/bin/env python3
"""Apply Alembic migrations using variables from the repo-root `.env` file.

Usage (from anywhere):
  python baseline/api_gateway/scripts/migrate.py
  python baseline/api_gateway/scripts/migrate.py current
  python baseline/api_gateway/scripts/migrate.py downgrade -1

Requires: `alembic` on PATH or run with api_gateway venv activated.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import sys

# Allow `import db.*` when run as a script from repo root.
_API = Path(__file__).resolve().parent.parent
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from db.dotenv_merge import load_dotenv_merged  # noqa: E402


def _api_gateway_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> None:
    load_dotenv_merged(_api_gateway_dir() / "db" / "migrations")
    api = _api_gateway_dir()
    args = sys.argv[1:] if len(sys.argv) > 1 else ["upgrade", "head"]
    venv_alembic = api / ".venv" / "bin" / "alembic"
    cmd = [str(venv_alembic), *args] if venv_alembic.is_file() else ["alembic", *args]
    raise SystemExit(subprocess.call(cmd, cwd=api))


if __name__ == "__main__":
    main()
