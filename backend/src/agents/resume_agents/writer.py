from typing import Any
from typing import Protocol

from .contracts import JobIR, ResumeIR, RewritePlan


class WritingModelClient(Protocol):
    def rewrite_resume(self, resume: dict[str, Any], job: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]: ...


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def rewrite_resume(resume: ResumeIR | dict[str, Any], job: JobIR | dict[str, Any], plan: RewritePlan | dict[str, Any], model_client: WritingModelClient) -> ResumeIR:
    resume_ir = _validate(ResumeIR, resume)
    job_ir = _validate(JobIR, job)
    plan_ir = _validate(RewritePlan, plan)
    candidate = model_client.rewrite_resume(resume_ir.model_dump(), job_ir.model_dump(), plan_ir.model_dump())
    if not isinstance(candidate, dict):
        raise ValueError("Writer returned a non-object ResumeIR")
    preserved = resume_ir.model_dump()
    for field in ("name", "email", "phone", "linkedin_url", "github_url", "raw_text", "work_experience", "education", "projects", "skills", "certifications"):
        value = candidate.get(field)
        if field == "name" and (not value or value == "Unknown"):
            candidate[field] = preserved[field]
        elif field == "raw_text" and value != preserved[field]:
            candidate[field] = preserved[field]
        elif field in {"work_experience", "education", "projects", "skills", "certifications"} and not value and preserved[field]:
            candidate[field] = preserved[field]
    return _validate(ResumeIR, candidate)