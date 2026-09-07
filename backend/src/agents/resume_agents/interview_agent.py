from typing import Any
from typing import Protocol

from .contracts import InterviewPrep, JobIR, ResumeIR


class InterviewModelClient(Protocol):
    def generate_interview_questions(self, resume: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]: ...


def _model_validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def generate_interview_questions(
    resume: ResumeIR | dict[str, Any],
    job: JobIR | dict[str, Any],
    model_client: InterviewModelClient,
) -> InterviewPrep:
    resume_ir = _model_validate(ResumeIR, resume)
    job_ir = _model_validate(JobIR, job)
    result = model_client.generate_interview_questions(resume_ir.model_dump(), job_ir.model_dump())
    return _model_validate(InterviewPrep, result)
