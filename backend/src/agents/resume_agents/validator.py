import re
from typing import Any

from .agentcore_client import AgentCoreClient
from .contracts import ResumeIR, ValidationIssue, ValidationReport


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def _flat(resume: ResumeIR) -> str:
    return " ".join(str(value) for value in resume.model_dump().values()).lower()


def validate_resume(authoritative_resume: ResumeIR | dict[str, Any], candidate_resume: ResumeIR | dict[str, Any], agentcore: AgentCoreClient | None = None) -> ValidationReport:
    authoritative = _validate(ResumeIR, authoritative_resume)
    candidate = _validate(ResumeIR, candidate_resume)
    if agentcore is not None:
        return _validate(ValidationReport, agentcore.validate_resume(authoritative.model_dump(), candidate.model_dump()))
    original_text = _flat(authoritative)
    issues: list[ValidationIssue] = []
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