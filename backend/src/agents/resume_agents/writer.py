from copy import deepcopy
from typing import Any

from .agentcore_client import AgentCoreClient
from .contracts import JobIR, ResumeIR, RewritePlan


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def rewrite_resume(resume: ResumeIR | dict[str, Any], job: JobIR | dict[str, Any], plan: RewritePlan | dict[str, Any], agentcore: AgentCoreClient | None = None) -> ResumeIR:
    resume_ir = _validate(ResumeIR, resume)
    job_ir = _validate(JobIR, job)
    plan_ir = _validate(RewritePlan, plan)
    if agentcore is not None:
        return _validate(ResumeIR, agentcore.rewrite_resume(resume_ir.model_dump(), job_ir.model_dump(), plan_ir.model_dump()))
    candidate = deepcopy(resume_ir.model_dump())
    candidate["skills"] = list(resume_ir.skills)
    return _validate(ResumeIR, candidate)