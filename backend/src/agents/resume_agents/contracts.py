from typing import Any

from pydantic import BaseModel, Field


class ResumeIR(BaseModel):
    name: str = "Unknown"
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    summary: str | None = None
    raw_text: str = ""
    work_experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    other_sections: dict[str, Any] = Field(default_factory=dict)


class JobIR(BaseModel):
    title: str
    company_name: str | None = None
    original_description: str
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    required_experience: list[str] = Field(default_factory=list)
    preferred_experience: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    technical_keywords: list[str] = Field(default_factory=list)
    domain_keywords: list[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    component_scores: dict[str, float] = Field(default_factory=dict)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_requirements: list[str] = Field(default_factory=list)
    partially_matched_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    keyword_analysis: dict[str, Any] = Field(default_factory=dict)
    supporting_resume_evidence: dict[str, list[str]] = Field(default_factory=dict)


class PlannedChange(BaseModel):
    target: str
    action: str
    priority: str
    reason: str
    instruction: str


class RewritePlan(BaseModel):
    changes: list[PlannedChange] = Field(default_factory=list)
    user_recommendations: list[str] = Field(default_factory=list)
    prohibited_claims: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    category: str
    claim: str
    reason: str


class ValidationReport(BaseModel):
    valid: bool
    unsupported_additions: list[ValidationIssue] = Field(default_factory=list)
    changed_dates: list[str] = Field(default_factory=list)
    inflated_titles: list[str] = Field(default_factory=list)
    summary: str = ""