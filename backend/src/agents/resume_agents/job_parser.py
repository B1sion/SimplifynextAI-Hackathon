import re
from typing import Any

from .agentcore_client import AgentCoreClient
from .contracts import JobIR


SKILL_TERMS = (
    "python", "sql", "java", "javascript", "typescript", "react", "node.js", "aws",
    "docker", "kubernetes", "terraform", "pandas", "spark", "machine learning", "git",
    "excel", "power bi", "airflow", "fastapi", "flask",
)


def parse_job(job: dict[str, Any], agentcore: AgentCoreClient | None = None) -> JobIR:
    """Create the JobIR used by the model prompts while preserving the raw description."""
    if agentcore is not None:
        result = agentcore.parse_job(job)
        return JobIR.model_validate(result)

    description = job.get("job_description") or ""
    lines = [" ".join(line.split()).strip(" -*") for line in description.splitlines() if line.strip()]
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    required_experience: list[str] = []
    preferred_experience: list[str] = []
    responsibilities: list[str] = []
    education_requirements: list[str] = []
    technical_keywords: list[str] = []

    for line in lines:
        lower = line.lower()
        preferred = any(term in lower for term in ("preferred", "nice to have", "bonus", "plus"))
        found = [term for term in SKILL_TERMS if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", lower)]
        for term in found:
            target = preferred_skills if preferred else required_skills
            if term not in target:
                target.append(term)
            if term not in technical_keywords:
                technical_keywords.append(term)
        if re.search(r"\b\d+\+?\s+years?\b", lower):
            (preferred_experience if preferred else required_experience).append(line)
        if any(term in lower for term in ("bachelor", "master", "degree", "certification")):
            education_requirements.append(line)
        if any(term in lower for term in ("responsibil", "build", "develop", "design", "lead", "manage", "maintain", "deliver")):
            responsibilities.append(line)

    return JobIR(
        title=job.get("job_title", "Untitled role"),
        company_name=job.get("company_name"),
        original_description=description,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        required_experience=required_experience,
        preferred_experience=preferred_experience,
        responsibilities=responsibilities,
        education_requirements=education_requirements,
        technical_keywords=technical_keywords,
    )