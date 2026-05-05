from __future__ import annotations

import re
from typing import Literal

AgentChannel = Literal["email", "linkedin", "company_site"]

PIPELINE_HINTS = (
    "pipeline summary",
    "pipeline status",
    "status mix",
    "application status",
    "show pipeline",
)
APPROVAL_HINTS = (
    "pending approvals",
    "approval queue",
    "approvals queue",
    "show approvals",
)
MATCH_HINTS = ("job matches", "top matches", "best matches", "fit matches", "match summary")
APPLICATION_HINTS = ("application detail", "application status", "show application", "latest application")
DRAFT_HINTS = ("create draft", "draft approval", "generate draft", "make draft", "new draft")
RECOMPUTE_HINTS = (
    "recompute",
    "rescore",
    "refresh match",
    "refresh scores",
    "refresh job scores",
    "update match scores",
)
RESUME_HINTS = (
    "resume summary",
    "parsed resume",
    "what's on my resume",
    "whats on my resume",
    "my resume profile",
    "profile snapshot",
    "resume on file",
)
PREP_SUMMARY_HINTS = (
    "prep summary",
    "my prep session",
    "show prep",
    "interview prep summary",
    "star stories",
    "company brief",
)
PREP_GENERATE_HINTS = (
    "generate prep",
    "regenerate prep",
    "build prep",
    "run prep generation",
    "create interview prep",
)
AUTOPILOT_HINTS = ("autopilot run", "batch run", "scoring run", "recent autopilot", "background run")
PIPELINE_RUN_HINTS = (
    "run job search pipeline",
    "full job search pipeline",
    "run the job search pipeline",
    "execute job search pipeline",
    "end-to-end job search",
    "run trading agents pipeline",
    "run pipeline runner",
)


def extract_limit(lower_text: str) -> int:
    m = re.search(r"\btop\s+(\d{1,2})\b", lower_text)
    if not m:
        m = re.search(r"\b(\d{1,2})\s+approvals?\b", lower_text)
    if not m:
        return 5
    try:
        value = int(m.group(1))
    except Exception:
        return 5
    return max(1, min(20, value))


def extract_application_id(text: str) -> str | None:
    m = re.search(r"\b(app_[a-zA-Z0-9]+)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", text)
    if m:
        return m.group(1)
    return None


def extract_job_id(text: str) -> str | None:
    m = re.search(r"\b(jb_[a-zA-Z0-9_]+)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", text)
    return m.group(1) if m else None


def extract_approval_id_only(text: str) -> str | None:
    m = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", text)
    return m.group(1) if m else None


def infer_channel(lower_text: str) -> AgentChannel | None:
    if "linkedin" in lower_text:
        return "linkedin"
    if "company site" in lower_text or "company_site" in lower_text or "company-site" in lower_text:
        return "company_site"
    if "email" in lower_text:
        return "email"
    return None
