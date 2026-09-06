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
    return _validate(ResumeIR, model_client.rewrite_resume(resume_ir.model_dump(), job_ir.model_dump(), plan_ir.model_dump()))