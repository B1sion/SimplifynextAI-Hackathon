from typing import Any

from src.Tools.job_tools import get_all_jobs
from src.agents.resume_agents.bedrock_client import BedrockClientError
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job


def resume_for_evaluator(resume: dict[str, Any]) -> dict[str, Any]:
    """`get_full_resume` returns `skills` as a list of dicts (`name`, `evidence`,
    ...) for the presenter layer, but `ResumeIR.skills` (the evaluator's
    contract) requires `list[str]`. Adapt just that field for the evaluator
    without mutating the caller's resume dict, so presenter code downstream
    keeps seeing the richer skill dicts it needs."""
    skills = resume.get("skills") or []
    skill_names = [skill.get("name", "") if isinstance(skill, dict) else str(skill) for skill in skills]
    return {**resume, "skills": skill_names}


def rank_jobs_for_resume(resume: dict[str, Any] | None, model_client: Any) -> list[dict[str, Any]]:
    """Evaluate every stored job against `resume`. One job's Bedrock failure
    degrades that job to score=0.0/evaluation=None instead of raising, so the
    caller always gets a full list back."""
    jobs = get_all_jobs()
    ranked: list[dict[str, Any]] = []
    evaluator_resume = resume_for_evaluator(resume) if resume is not None else None
    for job in jobs:
        entry = {**job, "score": 0.0, "evaluation": None}
        if evaluator_resume is not None:
            try:
                job_ir = parse_job(job)
                report = evaluate_resume(evaluator_resume, job_ir, model_client)
                entry["score"] = report.ats_score
                entry["evaluation"] = report
            except BedrockClientError:
                pass
        ranked.append(entry)
    return ranked
