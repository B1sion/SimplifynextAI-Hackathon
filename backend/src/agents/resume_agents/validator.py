import re
from typing import Any
from typing import Protocol

from .contracts import ResumeIR, ValidationIssue, ValidationReport


class ValidationModelClient(Protocol):
    def validate_resume(self, authoritative_resume: dict[str, Any], candidate_resume: dict[str, Any]) -> dict[str, Any]: ...


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def _flat(resume: ResumeIR) -> str:
    return " ".join(str(value) for value in resume.model_dump().values()).lower()


def validate_resume(authoritative_resume: ResumeIR | dict[str, Any], candidate_resume: ResumeIR | dict[str, Any], model_client: ValidationModelClient | None = None) -> ValidationReport:
    authoritative = _validate(ResumeIR, authoritative_resume)
    candidate = _validate(ResumeIR, candidate_resume)
    structural_issues: list[ValidationIssue] = []
    original_entries = [
        (str(item.get("company_name") or ""), str(item.get("job_title") or ""))
        for item in authoritative.work_experience
    ]
    candidate_entries = [
        (str(item.get("company_name") or ""), str(item.get("job_title") or ""))
        for item in candidate.work_experience
    ]
    if candidate_entries != original_entries:
        structural_issues.append(ValidationIssue(
            category="changed_experience_structure",
            claim="work_experience order or entries",
            reason="Employer and title sequence must remain unchanged so duplicate employers cannot be mixed up.",
        ))
    for field in ("education", "projects"):
        if len(getattr(candidate, field)) != len(getattr(authoritative, field)):
            structural_issues.append(ValidationIssue(
                category="changed_section_structure",
                claim=field,
                reason=f"{field} entries must be preserved unless explicitly supported by the rewrite plan.",
            ))
    if model_client is not None:
        report = _validate(ValidationReport, model_client.validate_resume(authoritative.model_dump(), candidate.model_dump()))
        if structural_issues:
            report.unsupported_additions.extend(structural_issues)
            report.valid = False
            report.summary = report.summary or "Candidate changes the authoritative resume structure"
        return report
    original_text = _flat(authoritative)
    issues: list[ValidationIssue] = structural_issues
    for skill in candidate.skills:
        if skill.lower() not in original_text:
            issues.append(ValidationIssue(category="invented_skill", claim=skill, reason="Skill is absent from authoritative resume"))
    original_experience = {str(item.get("company_name")) + str(item.get("job_title")) for item in authoritative.work_experience}
    for item in candidate.work_experience:
        identity = str(item.get("company_name")) + str(item.get("job_title"))
        if identity not in original_experience:
            issues.append(ValidationIssue(category="invented_responsibility", claim=identity, reason="Experience entry is absent from authoritative resume"))
        for key in ("start_date", "end_date"):
            original_dates = {entry.get(key) for entry in authoritative.work_experience}
            if item.get(key) not in original_dates:
                issues.append(ValidationIssue(category="changed_date", claim=str(item.get(key)), reason=f"{key} is not supported by authoritative resume"))
    changed_dates = [issue.claim for issue in issues if issue.category == "changed_date"]
    return ValidationReport(valid=not issues, unsupported_additions=issues, changed_dates=changed_dates, summary="Candidate is truthful" if not issues else "Candidate contains unsupported additions")