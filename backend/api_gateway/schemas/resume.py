from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SeniorityLevel = Literal["Junior", "Mid", "Senior", "Lead", "Staff", "Principal"]


class ParsedProfileModel(BaseModel):
    name: str = ""
    headline: str = ""
    experience_years: float = 0
    skills: list[str] = Field(default_factory=list)
    top_skills: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    summary: str = ""


class UserPreferencesModel(BaseModel):
    target_role: str = ""
    location: str = ""
    min_salary: int | None = None
    seniority: SeniorityLevel = "Mid"
    skills: list[str] = Field(default_factory=list)
    excluded_companies: list[str] | None = None


class UserPreferencesPatch(BaseModel):
    """Partial update body for PATCH /me/preferences."""

    target_role: str | None = None
    location: str | None = None
    min_salary: int | None = None
    seniority: SeniorityLevel | None = None
    skills: list[str] | None = None
    excluded_companies: list[str] | None = None


class ResumeProfileResponse(BaseModel):
    id: str
    storage_path: str
    file_name: str
    parsed_profile: ParsedProfileModel
    preferences: UserPreferencesModel
    version: int
    created_at: datetime


class ResumeAnalyzeResponse(BaseModel):
    analysis: str


OnboardingState = Literal["no_resume", "scoring_in_progress", "ready"]
OnboardingStep = Literal["upload_complete", "parsing_resume", "scoring_job_matches", "building_first_queue", "first_jobs_ready"]


class OnboardingStatusResponse(BaseModel):
    state: OnboardingState
    current_step: OnboardingStep
    eta_seconds: int | None = None
    has_resume: bool
    first_jobs_ready: bool
