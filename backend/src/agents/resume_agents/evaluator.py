from typing import Any
from typing import Protocol

from .contracts import ATSReport, JobIR, ResumeIR


class EvaluationModelClient(Protocol):
    def evaluate_resume(self, resume: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]: ...


def _model_validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def evaluate_resume(resume: ResumeIR | dict[str, Any], job: JobIR | dict[str, Any], model_client: EvaluationModelClient) -> ATSReport:
    resume_ir = _model_validate(ResumeIR, resume)
    job_ir = _model_validate(JobIR, job)
    result = model_client.evaluate_resume(resume_ir.model_dump(), job_ir.model_dump())
    if "ats_score" not in result and "overall_score" in result:
        result = {**result, "ats_score": result["overall_score"]}
    return _model_validate(ATSReport, result)