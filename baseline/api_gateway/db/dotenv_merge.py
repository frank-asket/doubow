"""Load multiple `.env` files along a directory chain (child → parents).

Later files in the chain override earlier ones so the repository root `.env`
wins over `baseline/.env` when both exist.
"""

from __future__ import annotations

import os
from pathlib import Path


def iter_dotenv_paths_upward(start_dir: Path) -> list[Path]:
    paths: list[Path] = []
    p = start_dir.resolve()
    for _ in range(32):
        cand = p / ".env"
        if cand.is_file():
            paths.append(cand)
        if p.parent == p:
            break
        p = p.parent
    return paths


def load_dotenv_merged(start_dir: Path) -> None:
    for env_path in iter_dotenv_paths_upward(start_dir):
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, _, v = s.partition("=")
            os.environ[k.strip()] = v.strip().strip('"').strip("'")
