from typing import Any
from typing import Protocol

from .contracts import InterviewPrep, InterviewValidationReport, JobIR, ResumeIR


class InterviewValidationModelClient(Protocol):
    def validate_interview(self, resume: dict[str, Any], job: dict[str, Any], interview_prep: dict[str, Any]) -> dict[str, Any]: ...


def _model_validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def validate_interview(
    resume: ResumeIR | dict[str, Any],
    job: JobIR | dict[str, Any],
    prep: InterviewPrep,
    model_client: InterviewValidationModelClient,
) -> InterviewValidationReport:
    """Ask the interview validator agent whether each drafted answer is truthful.

    This layer intentionally performs no Python claim matching. The validation
    agent is the authority for subjective truthfulness decisions; the wrapper
    only validates the response shape.
    """
    resume_ir = _model_validate(ResumeIR, resume)
    job_ir = _model_validate(JobIR, job)
    result = model_client.validate_interview(resume_ir.model_dump(), job_ir.model_dump(), prep.model_dump())
    return _model_validate(InterviewValidationReport, result)
