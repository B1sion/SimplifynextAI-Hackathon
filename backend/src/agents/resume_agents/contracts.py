from typing import Any

from pydantic import BaseModel, Field


class ResumeIR(BaseModel):
    name: str = "Unknown"
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    other_urls: list[str] = Field(default_factory=list)
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


class ATSReport(BaseModel):
    ats_score: float = Field(ge=0, le=100)
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    keyword_gaps: list[str] = Field(default_factory=list)
    experience_gaps: list[str] = Field(default_factory=list)
    ats_issues: list[str] = Field(default_factory=list)
    high_priority_improvements: list[str] = Field(default_factory=list)

    @property
    def overall_score(self) -> float:
        """Compatibility accessor for existing API callers."""
        return self.ats_score


EvaluationReport = ATSReport


class PlannedChange(BaseModel):
    section: str = ""
    target: str
    priority: str
    action: str
    instruction: str
    reason: str


class RewritePlan(BaseModel):
    strategy: str = ""
    changes: list[PlannedChange] = Field(default_factory=list)
    skills_to_emphasize: list[str] = Field(default_factory=list)
    keywords_to_integrate: list[str] = Field(default_factory=list)
    information_not_to_invent: list[str] = Field(default_factory=list)
    user_suggestions: list[str] = Field(default_factory=list)


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


class RecoveryDirective(BaseModel):
    failure_type: str
    summary: str = ""
    validation_failures: list[str] = Field(default_factory=list)
    facts_to_restore: list[str] = Field(default_factory=list)
    facts_to_preserve: list[str] = Field(default_factory=list)
    unsupported_content_to_remove: list[str] = Field(default_factory=list)
    planner_corrections: list[str] = Field(default_factory=list)
    writer_constraints: list[str] = Field(default_factory=list)
    retry_strategy: str = ""