from typing import Any, Protocol

from src.Tools.evaluation_tools import save_evaluation
from src.Tools.job_tools import get_job
from src.Tools.optimization_tools import (
    complete_optimization_run,
    create_optimization_run,
    create_resume_version,
    fail_optimization_run,
    increment_iteration,
    set_optimization_scores,
    update_resume_version_rendered_path,
    update_optimization_status,
)
from src.Tools.plan_tools import save_rewrite_plan
from src.Tools.resume_tools import get_full_resume
from .evaluator import evaluate_resume
from .job_parser import parse_job
from .planner import plan_resume
from .validator import validate_resume
from .writer import rewrite_resume
from .contracts import JobIR, RecoveryDirective, ResumeIR, RewritePlan, ValidationReport
from src.services.resume_renderer import render_resume_pdf


class OrchestratingModelClient(Protocol):
    def orchestrate(self, state: dict[str, Any]) -> dict[str, Any]: ...


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def _fallback_recovery(
    authoritative: ResumeIR,
    current: ResumeIR,
    validation: ValidationReport,
) -> RecoveryDirective:
    failures = [issue.claim or issue.reason for issue in validation.unsupported_additions]
    failures.extend(validation.changed_dates)
    facts_to_restore = []
    for field in ("email", "phone", "linkedin_url", "github_url", "work_experience", "education", "projects", "skills", "certifications"):
        if getattr(authoritative, field) and not getattr(current, field):
            facts_to_restore.append(field)
    return RecoveryDirective(
        failure_type="structural" if facts_to_restore else "mixed",
        summary=validation.summary,
        validation_failures=failures,
        facts_to_restore=facts_to_restore,
        facts_to_preserve=["all authoritative contact fields, employers, titles, dates, education, projects, skills, and certifications"],
        unsupported_content_to_remove=failures,
        planner_corrections=["Only target presentation or bullets supported by the authoritative ResumeIR."],
        writer_constraints=["Return every authoritative section and preserve untouched fields exactly."],
        retry_strategy="Regenerate the plan with this directive, then retry the writer before persisting anything.",
    )


def recover(
    authoritative: ResumeIR | dict[str, Any],
    current: ResumeIR | dict[str, Any],
    job: JobIR | dict[str, Any],
    plan: RewritePlan | dict[str, Any],
    validation: ValidationReport | dict[str, Any],
    model_client: OrchestratingModelClient,
) -> RecoveryDirective:
    authoritative_ir = _validate(ResumeIR, authoritative)
    current_ir = _validate(ResumeIR, current)
    job_ir = _validate(JobIR, job)
    plan_ir = _validate(RewritePlan, plan)
    validation_report = _validate(ValidationReport, validation)
    if not hasattr(model_client, "orchestrate"):
        return _fallback_recovery(authoritative_ir, current_ir, validation_report)
    result = model_client.orchestrate(
        {
            "authoritative_resume": authoritative_ir.model_dump(),
            "current_resume": current_ir.model_dump(),
            "job": job_ir.model_dump(),
            "rewrite_plan": plan_ir.model_dump(),
            "validation_report": validation_report.model_dump(),
        }
    )
    return _validate(RecoveryDirective, result)


class ResumeOptimizationOrchestrator:
    """Coordinate the specialist agents and gate all persisted candidates."""

    def __init__(self, model_client: Any, max_retries_per_iteration: int = 2):
        self.model_client = model_client
        self.max_retries_per_iteration = max_retries_per_iteration

    def run(
        self,
        resume_id: int,
        job_id: int,
        max_iterations: int = 3,
        min_score_improvement: float = 2,
        target_score: float = 85,
    ) -> dict[str, Any]:
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
            version = create_resume_version(run["id"], current, parent_version_id=None, version_number=0)
            evaluation = evaluate_resume(current, job_ir, self.model_client)
            initial_saved = save_evaluation(run["id"], version["id"], 0, evaluation.ats_score, evaluation.model_dump())
            previous_score = evaluation.ats_score
            set_optimization_scores(run["id"], initial_score=previous_score, current_score=previous_score)
            initial_history = evaluation.model_dump()
            initial_history["_evaluation_id"] = initial_saved["id"]
            history = [initial_history]

            for iteration in range(1, max_iterations + 1):
                if previous_score >= target_score:
                    break
                recovery_directive = None
                candidate = None
                validation = None
                plan = None
                for _attempt in range(self.max_retries_per_iteration + 1):
                    plan = plan_resume(current, job_ir, evaluation, self.model_client, recovery_directive)
                    save_rewrite_plan(run["id"], history[-1].get("_evaluation_id", 0), version["id"], iteration - 1, plan.model_dump())
                    if not plan.changes:
                        break
                    candidate = rewrite_resume(current, job_ir, plan, self.model_client)
                    validation = validate_resume(authoritative, candidate, self.model_client)
                    if validation.valid:
                        break
                    recovery_directive = recover(authoritative, current, job_ir, plan, validation, self.model_client)

                if plan is None or not plan.changes:
                    break
                if validation is None or not validation.valid:
                    failed = fail_optimization_run(run["id"])
                    return {
                        "run": failed,
                        "resume": current,
                        "evaluation": evaluation.model_dump(),
                        "validation": validation.model_dump() if validation else None,
                        "recovery": recovery_directive.model_dump() if recovery_directive else None,
                        "history": history,
                    }

                version = create_resume_version(run["id"], candidate.model_dump(), parent_version_id=version["id"])
                evaluation = evaluate_resume(candidate, job_ir, self.model_client)
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

            rendered_path = render_resume_pdf(current, run["id"], version["version_number"])
            update_resume_version_rendered_path(version["id"], str(rendered_path))
            completed = complete_optimization_run(run["id"], previous_score)
            return {
                "run": completed,
                "resume": current,
                "evaluation": evaluation.model_dump(),
                "history": history,
                "rendered_file_path": str(rendered_path),
            }
        except Exception:
            fail_optimization_run(run["id"])
            raise