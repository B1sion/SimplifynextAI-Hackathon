from typing import Any

from src.agents.resume_agents.bedrock_client import JsonModelClient
from src.agents.resume_agents.orchestrator import ResumeOptimizationOrchestrator


def optimize_resume(resume_id: int, job_id: int, model_client: JsonModelClient, max_iterations: int = 3, min_score_improvement: float = 2, target_score: float = 85) -> dict[str, Any]:
    return ResumeOptimizationOrchestrator(model_client).run(
        resume_id,
        job_id,
        max_iterations=max_iterations,
        min_score_improvement=min_score_improvement,
        target_score=target_score,
    )