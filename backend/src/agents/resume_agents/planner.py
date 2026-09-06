from typing import Any

from .agentcore_client import AgentCoreClient
from .contracts import EvaluationReport, JobIR, ResumeIR, RewritePlan


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def plan_resume(resume: ResumeIR | dict[str, Any], job: JobIR | dict[str, Any], evaluation: EvaluationReport | dict[str, Any], agentcore: AgentCoreClient | None = None) -> RewritePlan:
    resume_ir = _validate(ResumeIR, resume)
    job_ir = _validate(JobIR, job)
    evaluation_ir = _validate(EvaluationReport, evaluation)
    if agentcore is not None:
        return _validate(RewritePlan, agentcore.plan_resume(resume_ir.model_dump(), job_ir.model_dump(), evaluation_ir.model_dump()))
    changes = [
        {"target": f"skills.{skill}", "action": "emphasize", "priority": "high", "reason": "Required skill is missing from the evaluation", "instruction": f"Add only existing resume evidence for {skill}; do not claim new experience."}
        for skill in evaluation_ir.missing_skills
        if skill in job_ir.required_skills
    ]
    return RewritePlan(
        changes=changes,
        user_recommendations=evaluation_ir.recommendations,
        prohibited_claims=[f"Do not invent evidence for {skill}" for skill in evaluation_ir.missing_skills],
    )