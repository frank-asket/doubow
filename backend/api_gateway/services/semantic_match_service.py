"""Feature-flagged semantic matching helpers.

This module is optional at runtime. It lazy-loads sentence-transformers only
when semantic matching is enabled, and callers should gracefully fall back when
the dependency is unavailable.
"""

from __future__ import annotations

from functools import lru_cache
import re

from models.job import Job


class SemanticMatcherUnavailableError(RuntimeError):
    """Raised when sentence-transformers is unavailable."""


@lru_cache(maxsize=1)
def _get_sentence_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
        raise SemanticMatcherUnavailableError("sentence-transformers is not installed") from exc

    # Small default model for fast local experimentation.
    return SentenceTransformer("all-MiniLM-L6-v2")


def _profile_text(parsed_profile: dict | None) -> str:
    if not isinstance(parsed_profile, dict):
        return ""
    headline = str(parsed_profile.get("headline") or "").strip()
    summary = str(parsed_profile.get("summary") or "").strip()
    skills = [str(s).strip() for s in (parsed_profile.get("skills") or []) if str(s).strip()]
    parts = [p for p in (headline, summary, ", ".join(skills[:20])) if p]
    return "\n".join(parts)


def _job_text(job: Job) -> str:
    return "\n".join(
        p for p in (job.title, job.company, job.location or "", job.description or "") if p
    )


_TOKEN_RE = re.compile(r"[a-z][a-z0-9+.#-]{2,}")
_STOPWORDS = {
    "and",
    "the",
    "with",
    "for",
    "from",
    "that",
    "this",
    "your",
    "you",
    "our",
    "role",
    "job",
    "work",
    "team",
    "experience",
    "years",
    "school",
}


def _tokenize(text: str) -> set[str]:
    tokens = {m.group(0).lower() for m in _TOKEN_RE.finditer(text)}
    return {t for t in tokens if t not in _STOPWORDS}


def keyword_fit_score(parsed_profile: dict | None, job: Job) -> float | None:
    """Cheap lexical overlap fallback (1.0-5.0), used when embeddings are disabled."""
    profile = _profile_text(parsed_profile)
    posting = _job_text(job)
    if not profile or not posting:
        return None
    p_tokens = _tokenize(profile)
    j_tokens = _tokenize(posting)
    if not p_tokens or not j_tokens:
        return None

    overlap = len(p_tokens & j_tokens)
    if overlap == 0:
        return 1.0

    # Use profile coverage to avoid inflating large postings with sparse overlap.
    coverage = overlap / max(1, len(p_tokens))
    scaled = 1.0 + min(1.0, coverage) * 4.0
    return max(1.0, min(5.0, scaled))


def semantic_fit_score(parsed_profile: dict | None, job: Job) -> float | None:
    """Return a 1.0-5.0 semantic fit score or None when insufficient signal."""
    profile = _profile_text(parsed_profile)
    posting = _job_text(job)
    if not profile or not posting:
        return None

    model = _get_sentence_model()
    # Normalize embeddings so dot product approximates cosine similarity.
    emb_profile, emb_job = model.encode([profile, posting], normalize_embeddings=True)
    cosine = float(sum(a * b for a, b in zip(emb_profile, emb_job, strict=False)))
    cosine = max(-1.0, min(1.0, cosine))
    # Map cosine [-1, 1] to fit score [1, 5].
    scaled = 1.0 + ((cosine + 1.0) / 2.0) * 4.0
    return max(1.0, min(5.0, scaled))
