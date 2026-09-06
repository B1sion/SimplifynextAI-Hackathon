from typing import Any

from src.Tools.job_tools import get_all_jobs
from src.agents.resume_agents.bedrock_client import BedrockClientError
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job


def rank_jobs_for_resume(resume: dict[str, Any] | None, model_client: Any) -> list[dict[str, Any]]:
    """Evaluate every stored job against `resume`. One job's Bedrock failure
    degrades that job to score=0.0/evaluation=None instead of raising, so the
    caller always gets a full list back."""
    jobs = get_all_jobs()
    ranked: list[dict[str, Any]] = []
    for job in jobs:
        entry = {**job, "score": 0.0, "evaluation": None}
        if resume is not None:
            try:
                job_ir = parse_job(job)
                report = evaluate_resume(resume, job_ir, model_client)
                entry["score"] = report.ats_score
                entry["evaluation"] = report
            except BedrockClientError:
                pass
        ranked.append(entry)
    return ranked
