"""Deterministic pass/fail checks on model-generated text for CI and capstone eval evidence.

This is not a substitute for human judgment or LLM-as-judge; it enforces baseline
structure (non-empty, length bounds, runaway repetition) per use-case. See
``docs/capstone-readiness.md`` (generative rubric).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

UseCaseKey = Literal["chat", "drafts", "prep", "resume", "default"]

# Minimum visible characters after strip (rough lower bounds for “real” answers).
_MIN_LEN: dict[str, int] = {
    "chat": 8,
    "drafts": 120,
    "prep": 80,
    "resume": 60,
    "default": 20,
}

_MAX_LEN = 200_000
# If the same normalized sentence appears more than this count, flag as degenerate output.
_MAX_REPEAT_SENTENCE = 8


@dataclass
class GenerativeRubricResult:
    passed: bool
    use_case: str
    violations: list[str] = field(default_factory=list)


def _normalize_sentence(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _split_sentences(text: str) -> list[str]:
    # Lightweight split for repetition detection (no NLP dependency).
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def assess_generative_text(text: str | None, *, use_case: UseCaseKey | str | None = None) -> GenerativeRubricResult:
    """Return pass/fail with human-readable violation messages."""
    key = (use_case or "default").strip().lower()
    if key not in _MIN_LEN:
        key = "default"

    violations: list[str] = []

    if text is None:
        violations.append("output is None")
        return GenerativeRubricResult(passed=False, use_case=key, violations=violations)

    stripped = text.strip()
    if not stripped:
        violations.append("output is empty or whitespace-only")
        return GenerativeRubricResult(passed=False, use_case=key, violations=violations)

    if len(stripped) > _MAX_LEN:
        violations.append(f"output exceeds max length ({len(stripped)} > {_MAX_LEN})")

    min_len = _MIN_LEN[key]
    if len(stripped) < min_len:
        violations.append(f"output shorter than minimum for use_case={key} ({len(stripped)} < {min_len})")

    sentences = _split_sentences(stripped)
    if sentences:
        counts: dict[str, int] = {}
        for sent in sentences:
            norm = _normalize_sentence(sent)
            if len(norm) < 12:
                continue
            counts[norm] = counts.get(norm, 0) + 1
        for norm, n in counts.items():
            if n > _MAX_REPEAT_SENTENCE:
                violations.append(f"excessive repetition of sentence ({n}×): {norm[:80]}…")
                break

    passed = len(violations) == 0
    return GenerativeRubricResult(passed=passed, use_case=key, violations=violations)
