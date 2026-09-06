from typing import Any

from src.Tools.job_tools import get_all_jobs
from src.agents.resume_agents.bedrock_client import BedrockClientError
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job


def resume_for_evaluator(resume: dict[str, Any]) -> dict[str, Any]:
    """Adapt a `get_full_resume()`-shaped dict into the flat shape `ResumeIR`
    expects. Prefers the ingestion-time `resume["resume"]["resume_json"]`
    when present — it is already `ResumeIR`-shaped, with `skills: list[str]`
    and the real `name`/`raw_text`/`email` — since that is the richest source
    of truth for the evaluator. Falls back to rebuilding an equivalent
    payload from the nested `person`/`resume`/`skills` sub-objects when no
    `resume_json` was stored, converting only `skills` (`list[dict]` ->
    `list[str]`) so the caller's own dict (and presenter code downstream)
    keeps seeing the richer per-skill dicts it needs; this function never
    mutates its input."""
    resume_json = (resume.get("resume") or {}).get("resume_json")
    if isinstance(resume_json, dict):
        return resume_json

    person = resume.get("person") or {}
    resume_meta = resume.get("resume") or {}
    skills = resume.get("skills") or []
    skill_names = [skill.get("name", "") if isinstance(skill, dict) else str(skill) for skill in skills]
    return {
        "name": person.get("name") or resume_meta.get("name") or "Unknown",
        "email": person.get("email"),
        "phone": person.get("phone"),
        "linkedin_url": person.get("linkedin_url"),
        "github_url": person.get("github_url"),
        "portfolio_url": person.get("portfolio_url"),
        "raw_text": resume_meta.get("raw_text") or "",
        "work_experience": resume.get("work_experience") or [],
        "education": resume.get("education") or [],
        "projects": resume.get("projects") or [],
        "skills": skill_names,
    }


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
