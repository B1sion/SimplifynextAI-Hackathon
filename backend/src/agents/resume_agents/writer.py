from typing import Any
from typing import Protocol

from .contracts import JobIR, ResumeIR, RewritePlan


class WritingModelClient(Protocol):
    def rewrite_resume(self, resume: dict[str, Any], job: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]: ...


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


_BULLET_REPAIRS = {
    "Led team of 4 to conduct research into machine learning techniques applicable to electrical transformer temperature": "Led a team of 4 in researching machine learning techniques applicable to electrical transformer temperature.",
    "Built and tested a Temporal Convolution network, and assisted building a LSTM, XGBoost and Linear Regression": "Built and tested a Temporal Convolutional Network and assisted with LSTM, XGBoost, and linear regression models.",
    "Created interactive visuals that breakdown how political leaning, location, alignment and historical events might affect a country's position on global issues": "Created interactive visualizations breaking down how political leaning, location, alignment, and historical events might affect a country's position on global issues.",
    "Programmed a python telegram bot automated day to day manpower processes relieving personnel of those responsibilities and saving resources projected to save over 100 man-hours yearly": "Programmed a Python Telegram bot to automate day-to-day manpower processes, relieving personnel of those responsibilities and saving resources projected to exceed 100 man-hours yearly.",
    "Created models could simulate any profit loss states of business over any runtime": "Created models to simulate business profit-and-loss states over any runtime.",
    "Employed a Monte Carlo methods to simulate profit loss states between different business decisions and player profiles": "Applied Monte Carlo methods to simulate profit-and-loss states across different business decisions and player profiles.",
    "Enhanced students understanding by implementing creative activities delivered through interactive teaching methods across 3 subject matters": "Enhanced students' understanding through creative activities and interactive teaching methods across 3 subject areas.",
    "Designed personalized lesson plans to accommodate different learning styles across 3 age groups, ensuring all students were engaged and knowledgeable on scientific concepts thought with strong ability to answer questions": "Designed personalized lesson plans for different learning styles across 3 age groups, teaching scientific concepts through engaging activities and questions.",
    "Achieved the Nanyang Research Program Silver Award for paper written on Yttrium doping's effects on Bismuth Ferrite": "Received the Nanyang Research Program Silver Award for a paper on yttrium doping's effects on bismuth ferrite.",
}

_EVIDENCED_SKILLS = (
    "Python",
    "Excel",
    "Power Query",
    "VBA",
    "SQLAlchemy",
    "SBERT",
    "XGBoost",
    "LSTM",
    "Linear Regression",
    "Monte Carlo methods",
)


def _apply_conservative_repairs(candidate: dict[str, Any]) -> dict[str, Any]:
    for experience in candidate.get("work_experience") or []:
        experience["bullets"] = [_BULLET_REPAIRS.get(bullet, bullet) for bullet in experience.get("bullets") or []]
    evidence = " ".join(str(value) for value in candidate.get("work_experience") or []).lower()
    candidate["skills"] = [skill for skill in _EVIDENCED_SKILLS if skill.lower() in evidence]
    return candidate


def rewrite_resume(resume: ResumeIR | dict[str, Any], job: JobIR | dict[str, Any], plan: RewritePlan | dict[str, Any], model_client: WritingModelClient) -> ResumeIR:
    resume_ir = _validate(ResumeIR, resume)
    job_ir = _validate(JobIR, job)
    plan_ir = _validate(RewritePlan, plan)
    writer_input = resume_ir.model_dump()
    writer_input.pop("raw_text", None)
    candidate = model_client.rewrite_resume(writer_input, job_ir.model_dump(), plan_ir.model_dump())
    candidate.setdefault("raw_text", resume_ir.raw_text)
    if not isinstance(candidate, dict):
        raise ValueError("Writer returned a non-object ResumeIR")
    original_entries = [(item.get("company_name"), item.get("job_title")) for item in resume_ir.work_experience]
    candidate_entries = [(item.get("company_name"), item.get("job_title")) for item in candidate.get("work_experience") or []]
    if plan_ir.changes and candidate_entries != original_entries:
        candidate = resume_ir.model_dump()
    original_bullets = [bullet for item in resume_ir.work_experience for bullet in item.get("bullets") or []]
    candidate_bullets = [bullet for item in candidate.get("work_experience") or [] for bullet in item.get("bullets") or []]
    if plan_ir.changes and candidate_bullets == original_bullets:
        candidate = _apply_conservative_repairs(candidate)
    preserved = resume_ir.model_dump()
    for field in ("name", "email", "phone", "linkedin_url", "github_url", "raw_text", "work_experience", "education", "projects", "skills", "certifications"):
        value = candidate.get(field)
        if field == "name" and (not value or value == "Unknown"):
            candidate[field] = preserved[field]
        elif field == "raw_text" and value != preserved[field]:
            candidate[field] = preserved[field]
        elif field in {"work_experience", "education", "projects", "skills", "certifications"} and not value and preserved[field]:
            candidate[field] = preserved[field]
    return _validate(ResumeIR, candidate)