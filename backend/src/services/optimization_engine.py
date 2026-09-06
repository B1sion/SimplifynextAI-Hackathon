from typing import Any

from src.Tools.evaluation_tools import save_evaluation
from src.Tools.optimization_tools import (
    complete_optimization_run,
    create_optimization_run,
    create_resume_version,
    fail_optimization_run,
    increment_iteration,
    set_optimization_scores,
    update_optimization_status,
)
from src.Tools.plan_tools import save_rewrite_plan
from src.Tools.job_tools import get_job
from src.Tools.resume_tools import get_full_resume
from src.agents.resume_agents.bedrock_client import BedrockNovaClient
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job
from src.agents.resume_agents.planner import plan_resume
from src.agents.resume_agents.validator import validate_resume
from src.agents.resume_agents.writer import rewrite_resume


def optimize_resume(resume_id: int, job_id: int, model_client: BedrockNovaClient, max_iterations: int = 3, min_score_improvement: float = 2, target_score: float = 85) -> dict[str, Any]:
    original = get_full_resume(resume_id)
    job = get_job(job_id)
    if original is None or job is None:
        raise ValueError("Resume and job are required")
    run = create_optimization_run(resume_id, job_id, max_iterations=max_iterations)
    update_optimization_status(run["id"], "running")
    authoritative = original["resume"].get("resume_json") or original
    current = authoritative
    try:
        job_ir = parse_job(job)
		# Version 0 is immutable: every accepted candidate gets its own child version.
        version = create_resume_version(run["id"], current, parent_version_id=None, version_number=0)
        evaluation = evaluate_resume(current, job_ir, model_client)
        initial_saved = save_evaluation(run["id"], version["id"], 0, evaluation.ats_score, evaluation.model_dump())
        previous_score = evaluation.ats_score
        set_optimization_scores(run["id"], initial_score=previous_score, current_score=previous_score)
        initial_history = evaluation.model_dump()
        initial_history["_evaluation_id"] = initial_saved["id"]
        history = [initial_history]
        for iteration in range(1, max_iterations + 1):
            if previous_score >= target_score:
                break
            plan = plan_resume(current, job_ir, evaluation, model_client)
            save_rewrite_plan(run["id"], history[-1].get("_evaluation_id", 0), version["id"], iteration - 1, plan.model_dump())
            if not plan.changes:
                break
            candidate = rewrite_resume(current, job_ir, plan, model_client)
            validation = validate_resume(authoritative, candidate, model_client)
            if not validation.valid:
                failed = fail_optimization_run(run["id"])
                return {"run": failed, "resume": current, "evaluation": evaluation.model_dump(), "validation": validation.model_dump(), "history": history}
            version = create_resume_version(run["id"], candidate.model_dump(), parent_version_id=version["id"])
            evaluation = evaluate_resume(candidate, job_ir, model_client)
            saved = save_evaluation(run["id"], version["id"], iteration, evaluation.ats_score, evaluation.model_dump())
            evaluation_data = evaluation.model_dump()
            evaluation_data["_evaluation_id"] = saved["id"]
            history.append(evaluation_data)
            current = candidate.model_dump()
            improvement = evaluation.ats_score - previous_score
            increment_iteration(run["id"])
            previous_score = evaluation.ats_score
            set_optimization_scores(run["id"], current_score=previous_score)
            if evaluation.ats_score >= target_score or improvement < min_score_improvement:
                break
        completed = complete_optimization_run(run["id"], previous_score)
        return {"run": completed, "resume": current, "evaluation": evaluation.model_dump(), "history": history}
    except Exception:
        fail_optimization_run(run["id"])
        raise