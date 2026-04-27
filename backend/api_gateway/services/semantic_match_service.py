"""Feature-flagged semantic matching helpers.

This module is optional at runtime. It lazy-loads sentence-transformers only
when semantic matching is enabled, and callers should gracefully fall back when
the dependency is unavailable.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
import math
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


def _profile_skills(parsed_profile: dict | None) -> list[str]:
    if not isinstance(parsed_profile, dict):
        return []
    out: list[str] = []
    for raw in (parsed_profile.get("skills") or []):
        text = str(raw).strip().lower()
        if text:
            out.append(text)
    return out


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

_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sales": ("account executive", "sales", "business development", "partnership"),
    "marketing": ("marketing", "growth", "brand", "communications", "content"),
    "finance": ("finance", "fp&a", "accounting", "controller", "payroll", "tax"),
    "operations": ("operations", "program manager", "logistics", "procurement", "strategy"),
    "hr": ("people", "talent", "recruit", "human resources", "hrbp"),
    "customer_success": ("customer success", "support", "customer experience"),
    "software": ("software engineer", "backend", "frontend", "full stack", "sre", "devops"),
    "data": ("data", "analytics", "machine learning", "ai", "scientist", "ml"),
    "security": ("security", "trust", "fraud", "governance", "compliance"),
    "design": ("designer", "ux", "product design", "research"),
    "product": ("product manager", "product lead", "product"),
}
_NON_TECH_DOMAINS = {"sales", "marketing", "finance", "operations", "hr", "customer_success", "design"}
_TECH_DOMAINS = {"software", "data", "security"}


def _tokenize(text: str) -> set[str]:
    tokens = {m.group(0).lower() for m in _TOKEN_RE.finditer(text)}
    return {t for t in tokens if t not in _STOPWORDS}


def _vectorize_tokens(tokens: set[str]) -> Counter[str]:
    return Counter(tokens)


def _char_ngrams(text: str, n: int = 3) -> Counter[str]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    if len(normalized) < n:
        return Counter({normalized: 1}) if normalized else Counter()
    grams = [normalized[i : i + n] for i in range(0, len(normalized) - n + 1)]
    return Counter(grams)


def _cosine(counter_a: Counter[str], counter_b: Counter[str]) -> float:
    if not counter_a or not counter_b:
        return 0.0
    dot = sum(v * counter_b.get(k, 0) for k, v in counter_a.items())
    norm_a = math.sqrt(sum(v * v for v in counter_a.values()))
    norm_b = math.sqrt(sum(v * v for v in counter_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def _map_unit_to_fit(unit: float) -> float:
    return max(1.0, min(5.0, 1.0 + max(0.0, min(1.0, unit)) * 4.0))


def _infer_domain(text: str) -> str | None:
    lower = text.lower()
    best_domain: str | None = None
    best_score = 0
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > best_score:
            best_score = score
            best_domain = domain
    return best_domain if best_score > 0 else None


def _profile_domain(parsed_profile: dict | None) -> str | None:
    profile = _profile_text(parsed_profile)
    skills = ", ".join(_profile_skills(parsed_profile))
    return _infer_domain(f"{profile}\n{skills}")


def _job_domain(job: Job) -> str | None:
    return _infer_domain(f"{job.title}\n{job.description or ''}")


def _apply_domain_calibration(base_fit: float, parsed_profile: dict | None, job: Job) -> float:
    profile_domain = _profile_domain(parsed_profile)
    candidate_domain = _job_domain(job)
    if not profile_domain or not candidate_domain:
        return max(1.0, min(5.0, base_fit))

    adjusted = base_fit
    if profile_domain == candidate_domain:
        adjusted += 0.75
    elif profile_domain in _NON_TECH_DOMAINS and candidate_domain in _TECH_DOMAINS:
        adjusted -= 1.0
    elif profile_domain in _TECH_DOMAINS and candidate_domain in _NON_TECH_DOMAINS:
        adjusted -= 0.35
    elif profile_domain in _NON_TECH_DOMAINS and candidate_domain in _NON_TECH_DOMAINS:
        adjusted -= 0.2
    elif profile_domain in _TECH_DOMAINS and candidate_domain in _TECH_DOMAINS:
        adjusted -= 0.15
    else:
        adjusted -= 0.1

    return max(1.0, min(5.0, adjusted))


def keyword_fit_score(parsed_profile: dict | None, job: Job) -> float | None:
    """Weighted lexical fit (1.0-5.0) tuned for mixed tech/non-tech roles."""
    profile = _profile_text(parsed_profile)
    posting = _job_text(job)
    if not profile or not posting:
        return None
    profile_skills = _profile_skills(parsed_profile)
    p_tokens = _tokenize(profile)
    j_tokens = _tokenize(posting)
    title_tokens = _tokenize(job.title or "")
    if not p_tokens or not j_tokens:
        return None

    overlap_tokens = p_tokens & j_tokens
    overlap = len(overlap_tokens)
    if overlap == 0 and not profile_skills:
        return 1.0

    coverage = overlap / max(1, len(p_tokens))
    precision = overlap / max(1, len(j_tokens))
    jaccard = overlap / max(1, len(p_tokens | j_tokens))
    title_alignment = len(p_tokens & title_tokens) / max(1, len(title_tokens))

    # Phrase-level boost so non-tech profile skills still matter when tokens are sparse.
    posting_lower = posting.lower()
    skill_hits = sum(1 for skill in profile_skills if skill in posting_lower)
    skill_ratio = skill_hits / max(1, min(8, len(profile_skills)))

    unit = (
        0.35 * coverage
        + 0.20 * precision
        + 0.20 * jaccard
        + 0.20 * title_alignment
        + 0.05 * skill_ratio
    )
    return _apply_domain_calibration(_map_unit_to_fit(unit), parsed_profile, job)


def _lightweight_semantic_fit(parsed_profile: dict | None, job: Job) -> float | None:
    profile = _profile_text(parsed_profile)
    posting = _job_text(job)
    if not profile or not posting:
        return None

    # Guardrail: never regress below lexical quality when transformer embeddings
    # are unavailable in the runtime.
    lexical = keyword_fit_score(parsed_profile, job)
    profile_tokens = _tokenize(profile)
    posting_tokens = _tokenize(posting)
    token_cos = _cosine(_vectorize_tokens(profile_tokens), _vectorize_tokens(posting_tokens))
    ngram_cos = _cosine(_char_ngrams(profile), _char_ngrams(posting))
    unit = ((token_cos + 1.0) / 2.0) * 0.65 + ((ngram_cos + 1.0) / 2.0) * 0.35
    fallback_semantic = _map_unit_to_fit(unit)
    best = fallback_semantic if lexical is None else max(lexical, fallback_semantic)
    return _apply_domain_calibration(best, parsed_profile, job)


def semantic_fit_score(parsed_profile: dict | None, job: Job) -> float | None:
    """Return a 1.0-5.0 semantic fit score or None when insufficient signal."""
    profile = _profile_text(parsed_profile)
    posting = _job_text(job)
    if not profile or not posting:
        return None

    try:
        model = _get_sentence_model()
    except SemanticMatcherUnavailableError:
        return _lightweight_semantic_fit(parsed_profile, job)
    # Normalize embeddings so dot product approximates cosine similarity.
    emb_profile, emb_job = model.encode([profile, posting], normalize_embeddings=True)
    cosine = float(sum(a * b for a, b in zip(emb_profile, emb_job, strict=False)))
    cosine = max(-1.0, min(1.0, cosine))
    return _apply_domain_calibration(_map_unit_to_fit((cosine + 1.0) / 2.0), parsed_profile, job)
