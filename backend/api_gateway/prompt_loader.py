"""Load LLM system prompts from versioned text assets under ``prompts/``.

Templates may include ``{{GROUNDING}}``, substituted from ``grounding_rules.txt``.
"""

from __future__ import annotations

import functools
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def prompts_dir() -> Path:
    return _PROMPTS_DIR


@functools.lru_cache(maxsize=64)
def load_prompt_text(filename: str) -> str:
    """Return UTF-8 text from ``api_gateway/prompts/<filename>``."""
    path = _PROMPTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file missing: {path}")
    return path.read_text(encoding="utf-8").strip()


def load_prompt_with_grounding(filename: str) -> str:
    """Substitute ``{{GROUNDING}}`` with grounding rules; strip result."""
    raw = load_prompt_text(filename)
    grounding = load_prompt_text("grounding_rules.txt")
    return raw.replace("{{GROUNDING}}", grounding).strip()
