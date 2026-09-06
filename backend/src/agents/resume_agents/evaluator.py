import re
from typing import Any

from .agentcore_client import AgentCoreClient
from .contracts import EvaluationReport, JobIR, ResumeIR


def _model_validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def _as_text(resume: ResumeIR) -> str:
    parts = [resume.raw_text, *resume.skills]
    for experience in resume.work_experience:
        parts.extend(str(value) for value in experience.values() if value)
    for section in (resume.education, resume.projects):
        for item in section:
            parts.extend(str(value) for value in item.values() if value)
    return " ".join(parts).lower()


def _matches(term: str, text: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", text) is not None


def _local_evaluation(resume: ResumeIR, job: JobIR) -> EvaluationReport:
    text = _as_text(resume)
    matched = [skill for skill in job.required_skills + job.preferred_skills if _matches(skill, text)]
    missing = [skill for skill in job.required_skills if skill not in matched]
    preferred_missing = [skill for skill in job.preferred_skills if skill not in matched]
    required_total = len(job.required_skills)
    skill_score = 100.0 if not required_total else 100 * (required_total - len(missing)) / required_total
    experience_matches = [item for item in job.required_experience if any(_matches(word, text) for word in item.split() if len(word) > 3)]
    requirement_score = 100.0 if not job.required_experience else 100 * len(experience_matches) / len(job.required_experience)
    education_matches = [item for item in job.education_requirements if any(_matches(word, text) for word in item.split() if len(word) > 3)]
    education_score = 100.0 if not job.education_requirements else 100 * len(education_matches) / len(job.education_requirements)
    score = round(skill_score * 0.6 + requirement_score * 0.25 + education_score * 0.15, 2)
    evidence = {skill: [skill] for skill in matched}
    return EvaluationReport(
        overall_score=score,
        component_scores={"skills": round(skill_score, 2), "experience": round(requirement_score, 2), "education": round(education_score, 2)},
        matched_skills=matched,
        missing_skills=missing + preferred_missing,
        matched_requirements=experience_matches + education_matches,
        partially_matched_requirements=[],
        missing_requirements=[item for item in job.required_experience + job.education_requirements if item not in experience_matches + education_matches],
        strengths=[f"Matched {len(matched)} listed skills"],
        weaknesses=[f"Missing required skill: {skill}" for skill in missing],
        recommendations=[f"Add truthful evidence for {skill}" for skill in missing],
        keyword_analysis={"matched": matched, "missing": missing + preferred_missing},
        supporting_resume_evidence=evidence,
    )


def evaluate_resume(resume: ResumeIR | dict[str, Any], job: JobIR | dict[str, Any], agentcore: AgentCoreClient | None = None) -> EvaluationReport:
    resume_ir = _model_validate(ResumeIR, resume)
    job_ir = _model_validate(JobIR, job)
    local = _local_evaluation(resume_ir, job_ir)
    if agentcore is None:
        return local
    remote = _model_validate(EvaluationReport, agentcore.evaluate_resume(resume_ir.model_dump(), job_ir.model_dump()))
    remote.component_scores = remote.component_scores or local.component_scores
    remote.keyword_analysis = remote.keyword_analysis or local.keyword_analysis
    remote.supporting_resume_evidence = remote.supporting_resume_evidence or local.supporting_resume_evidence
    return remote