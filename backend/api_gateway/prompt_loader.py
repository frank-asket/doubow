"""Load LLM system prompts from versioned text assets under ``prompts/``.

Templates may include ``{{GROUNDING}}``, substituted from ``grounding_rules.txt``.

Full lines starting with ``#`` (after whitespace) are treated as editor comments and
removed before any prompt is returned — they never reach the LLM.
"""

from __future__ import annotations

import functools
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def prompts_dir() -> Path:
    return _PROMPTS_DIR


def _strip_full_line_hash_comments(text: str) -> str:
    """Drop lines whose first non-whitespace character is ``#`` (editor notes, not LLM content)."""
    out: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        out.append(line)
    return "\n".join(out).strip()


@functools.lru_cache(maxsize=64)
def load_prompt_text(filename: str) -> str:
    """Return UTF-8 text from ``api_gateway/prompts/<filename>``."""
    path = _PROMPTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file missing: {path}")
    raw = path.read_text(encoding="utf-8")
    return _strip_full_line_hash_comments(raw)


def load_prompt_with_grounding(filename: str) -> str:
    """Substitute ``{{GROUNDING}}`` with grounding rules; strip result."""
    raw = load_prompt_text(filename)
    grounding = load_prompt_text("grounding_rules.txt")
    return raw.replace("{{GROUNDING}}", grounding).strip()
