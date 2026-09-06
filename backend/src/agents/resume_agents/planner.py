from typing import Any
from typing import Protocol

from .contracts import ATSReport, JobIR, RecoveryDirective, ResumeIR, RewritePlan


class PlanningModelClient(Protocol):
    def plan_resume(self, resume: dict[str, Any], job: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]: ...


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def plan_resume(
    resume: ResumeIR | dict[str, Any],
    job: JobIR | dict[str, Any],
    evaluation: ATSReport | dict[str, Any],
    model_client: PlanningModelClient,
    recovery_directive: RecoveryDirective | dict[str, Any] | None = None,
) -> RewritePlan:
    resume_ir = _validate(ResumeIR, resume)
    job_ir = _validate(JobIR, job)
    evaluation_ir = _validate(ATSReport, evaluation)
    evaluation_payload = evaluation_ir.model_dump()
    if recovery_directive is not None:
        directive = _validate(RecoveryDirective, recovery_directive)
        evaluation_payload["recovery_directive"] = directive.model_dump()
    result = model_client.plan_resume(resume_ir.model_dump(), job_ir.model_dump(), evaluation_payload)
    return _validate(RewritePlan, result)