import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database.database import initialize_database
from src.Tools.application_tools import get_applications_for_person
from src.Tools.evaluation_tools import save_evaluation
from src.Tools.job_tools import get_all_jobs, get_job
from src.Tools.optimization_tools import create_optimization_run, create_resume_version, get_optimization_context, get_resume_versions
from src.Tools.profile_tools import save_profile_answers
from src.Tools.resume_tools import get_full_resume, get_latest_resume, get_resume
from src.Tools.watch_tools import get_watch_settings, set_watch_enabled
from src.agents.resume_agents.bedrock_client import BedrockClientError, BedrockNovaClient
from src.agents.resume_agents.contracts import ATSReport
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job
from src.agents.resume_ingestion import ingest_resume
from src.services.action_center import build_blocked_claim, build_resume_diffs, build_skill_gaps, demo_tailor_fallback
from src.services.job_ranking import rank_jobs_for_resume, resume_for_evaluator
from src.services.optimization_engine import optimize_resume
from src.services.presenters import WORK_PASS_STUB, compute_compass_report, facts_to_groups, job_to_frontend, match_requirements_to_frontend, verdict_for_score
from src.services.resume_renderer import GENERATED_RESUMES_DIR


ROOT_DIR = Path(__file__).resolve().parents[2]
ORIGINAL_RESUMES_DIR = ROOT_DIR / "storage" / "original_resumes"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class SaveProfileBody(BaseModel):
	answers: dict[str, int]


class SetWatchBody(BaseModel):
	enabled: bool


_PROFILE_QUESTIONS: list[dict[str, Any]] = [
	{
		"id": "work-status",
		"question": "What is your work status in Singapore?",
		"options": ["Citizen or PR", "Needs an Employment Pass", "On a student pass"],
		"defaultPick": 1,
	},
	{
		"id": "qualification",
		"question": "Highest completed qualification",
		"options": ["Diploma", "Bachelor's", "Master's or above"],
		"defaultPick": 1,
	},
	{
		"id": "experience",
		"question": "Years of full-time work experience",
		"options": ["Under 1", "1 to 3", "3 to 5", "5 or more"],
		"defaultPick": 0,
	},
]


app = FastAPI(title="Simplify Resume API")

_ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
	if origin.strip()
]
app.add_middleware(
	CORSMiddleware,
	allow_origins=_ALLOWED_ORIGINS,
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)


def _resume_payload(resume_id: int) -> dict[str, Any]:
	resume = get_full_resume(resume_id)
	if resume is None:
		raise HTTPException(status_code=404, detail="Resume not found")
	return resume_for_evaluator(resume)


def _requirement_checklist(report: ATSReport) -> list[dict[str, str]]:
	matched = [{"text": item, "status": "matched"} for item in report.matched_skills]
	missing = [{"text": item, "status": "missing"} for item in report.missing_skills]
	return matched + missing


@app.on_event("startup")
def startup() -> None:
	initialize_database()
	ORIGINAL_RESUMES_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@app.get("/profile/questions")
def profile_questions() -> list[dict[str, Any]]:
	return _PROFILE_QUESTIONS


@app.put("/profile", status_code=204)
def save_profile(body: SaveProfileBody, resume_id: int | None = Query(default=None)) -> None:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	if resume_record is None:
		raise HTTPException(status_code=404, detail="No resume uploaded yet")
	save_profile_answers(resume_record["person_id"], body.answers)


@app.get("/watch")
def watch_feed(resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	if resume_id is not None:
		resume_record = get_resume(resume_id)
		if resume_record is None:
			raise HTTPException(status_code=404, detail="Resume not found")
	else:
		resume_record = get_latest_resume()
	enabled = False
	if resume_record is not None:
		enabled = get_watch_settings(resume_record["person_id"])["enabled"]
	return {
		"ranAt": "Not run yet",
		"postingsScanned": 0,
		"scope": "Overnight watch has not run yet.",
		"enabled": enabled,
		"events": [],
	}


@app.get("/session")
def session_summary(resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	if resume_id is not None:
		resume_record = get_resume(resume_id)
		if resume_record is None:
			raise HTTPException(status_code=404, detail="Resume not found")
	else:
		resume_record = get_latest_resume()
	if resume_record is None:
		return {"candidateName": "", "factsConfirmed": 0, "claimsBlocked": 0, "lastWatchRun": "Not run yet"}

	resume = get_full_resume(resume_record["id"])
	facts_confirmed = (
		len(resume.get("skills") or [])
		+ sum(len(experience.get("bullets") or []) for experience in (resume.get("work_experience") or []))
		+ len(resume.get("education") or [])
		+ len(resume.get("projects") or [])
	)
	return {
		"candidateName": (resume.get("person") or {}).get("name") or "",
		"factsConfirmed": facts_confirmed,
		"claimsBlocked": 0,
		"lastWatchRun": "Not run yet",
	}


@app.get("/applications")
def applications_tracker(resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	if resume_id is not None:
		resume_record = get_resume(resume_id)
		if resume_record is None:
			raise HTTPException(status_code=404, detail="Resume not found")
	else:
		resume_record = get_latest_resume()
	rows: list[dict[str, Any]] = []
	if resume_record is not None:
		rows = get_applications_for_person(resume_record["person_id"])

	applications = []
	for row in rows:
		job = get_job(row["job_id"])
		applications.append(
			{
				"id": str(row["id"]),
				"job": job["job_title"] if job else "",
				"company": (job.get("company_name") or "") if job else "",
				"sent": str(row["sent_at"]),
				"status": row["status"],
				"verdict": row["verdict"],
			}
		)

	return {
		"metrics": [{"value": str(len(applications)), "label": "applications sent"}],
		"applications": applications,
	}


@app.put("/watch", status_code=204)
def set_watch(body: SetWatchBody, resume_id: int | None = Query(default=None)) -> None:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	if resume_record is None:
		raise HTTPException(status_code=404, detail="No resume uploaded yet")
	set_watch_enabled(resume_record["person_id"], body.enabled)


@app.get("/jobs")
def list_jobs(resume_id: int | None = None, mode: str = "browse") -> list[dict[str, Any]]:
	if resume_id is not None:
		resume_record = get_resume(resume_id)
		if resume_record is None:
			raise HTTPException(status_code=404, detail="Resume not found")
	else:
		resume_record = get_latest_resume()
	resume = get_full_resume(resume_record["id"]) if resume_record is not None else None
	ranked = rank_jobs_for_resume(resume, BedrockNovaClient())
	jobs = [job_to_frontend(entry, entry["score"] if resume is not None else None) for entry in ranked]
	if mode == "close" and resume is not None:
		jobs.sort(key=lambda job: job["score"], reverse=True)
	else:
		jobs.sort(key=lambda job: job["title"].casefold())
	return jobs


@app.get("/jobs/summary")
def jobs_summary(resume_id: int | None = Query(default=None)) -> dict[str, int]:
	if resume_id is not None:
		resume_record = get_resume(resume_id)
		if resume_record is None:
			raise HTTPException(status_code=404, detail="Resume not found")
	else:
		resume_record = get_latest_resume()
	resume = get_full_resume(resume_record["id"]) if resume_record is not None else None
	ranked = rank_jobs_for_resume(resume, BedrockNovaClient())
	counts = {"v": 0, "c": 0, "b": 0}
	for entry in ranked:
		counts[verdict_for_score(entry["score"] if resume is not None else 0)] += 1
	return {
		"totalRoles": len(ranked),
		"canApply": counts["v"],
		"mightNotQualify": counts["c"],
		"cannotApply": counts["b"],
	}


_LEARNING_TIME_WEEKS: dict[str, int] = {
	"python": 4, "sql": 3, "docker": 4, "kubernetes": 6, "aws": 6, "react": 5,
	"excel": 2, "power query": 3, "vba": 3, "tableau": 3, "looker": 2, "dbt": 6,
	"amplitude": 3, "figma": 2, "git": 2, "linux": 4,
}
_DEFAULT_LEARNING_WEEKS = 4


@app.get("/jobs/unlocks")
def jobs_unlocks(resume_id: int | None = Query(default=None), limit: int = Query(default=5, ge=1, le=20)) -> list[dict[str, Any]]:
	if resume_id is not None:
		resume_record = get_resume(resume_id)
		if resume_record is None:
			raise HTTPException(status_code=404, detail="Resume not found")
	else:
		resume_record = get_latest_resume()
	resume = get_full_resume(resume_record["id"]) if resume_record is not None else None
	ranked = rank_jobs_for_resume(resume, BedrockNovaClient())
	missing: set[str] = set()
	for entry in ranked:
		if entry["evaluation"] is not None:
			missing.update(entry["evaluation"].missing_skills)

	all_jobs = get_all_jobs()
	counts: list[tuple[str, int]] = []
	for skill in missing:
		count = sum(1 for job in all_jobs if skill.casefold() in (job.get("job_description") or "").casefold())
		counts.append((skill, count))
	counts.sort(key=lambda item: item[1], reverse=True)
	top = counts[:limit]
	max_count = max((count for _, count in top), default=0)

	return [
		{
			"name": skill,
			"jobs": count,
			"weeks": f"{_LEARNING_TIME_WEEKS.get(skill.casefold(), _DEFAULT_LEARNING_WEEKS)} weeks",
			"pct": round((count / max_count) * 100) if max_count else 0,
		}
		for skill, count in top
	]


@app.get("/resumes/{resume_id}/facts")
def resume_facts(resume_id: int) -> list[dict[str, Any]]:
	resume = get_full_resume(resume_id)
	if resume is None:
		raise HTTPException(status_code=404, detail="Resume not found")
	return facts_to_groups(resume)


@app.get("/jobs/{job_id}/requirements")
def job_requirements(job_id: int, resume_id: int = Query(...)) -> dict[str, Any]:
	job = get_job(job_id)
	if job is None:
		raise HTTPException(status_code=404, detail="Job not found")
	try:
		report = evaluate_resume(_resume_payload(resume_id), parse_job(job), BedrockNovaClient())
	except BedrockClientError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error
	return {"jobId": str(job_id), "requirements": _requirement_checklist(report), "evaluation": report.model_dump()}


@app.get("/jobs/{job_id}/learning-gaps")
def job_learning_gaps(job_id: int, resume_id: int = Query(...)) -> dict[str, Any]:
	job = get_job(job_id)
	if job is None:
		raise HTTPException(status_code=404, detail="Job not found")
	try:
		report = evaluate_resume(_resume_payload(resume_id), parse_job(job), BedrockNovaClient())
	except BedrockClientError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error
	gaps = list(dict.fromkeys(report.missing_skills + report.keyword_gaps + report.experience_gaps))
	opportunities = [
		{"jobId": str(other["id"]), "title": other["job_title"], "company": other.get("company_name") or ""}
		for other in get_all_jobs()
		if other["id"] != job_id and any(gap.casefold() in (other.get("job_description") or "").casefold() for gap in gaps)
	]
	return {
		"jobId": str(job_id),
		"gaps": [{"skill": gap, "suggestion": f"Build or document truthful evidence for {gap}."} for gap in gaps],
		"opportunities": opportunities,
	}


@app.get("/jobs/{job_id}/compass")
def jobs_compass(job_id: int, resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	job = get_job(job_id)
	if job is None:
		raise HTTPException(status_code=404, detail="Job not found")
	if resume_id is not None:
		resume_full = get_full_resume(resume_id)
		if resume_full is None:
			raise HTTPException(status_code=404, detail="Resume not found")
	else:
		resume_summary = get_latest_resume()
		resume_full = get_full_resume(resume_summary["id"]) if resume_summary else None
	return compute_compass_report(job, resume_full)


@app.get("/optimization-runs/{run_id}")
def optimization_run(run_id: int) -> dict[str, Any]:
	context = get_optimization_context(run_id)
	if context is None:
		raise HTTPException(status_code=404, detail="Optimization run not found")
	return context


@app.get("/optimization-runs/{run_id}/versions")
def optimization_versions(run_id: int) -> dict[str, Any]:
	context = get_optimization_context(run_id)
	if context is None:
		raise HTTPException(status_code=404, detail="Optimization run not found")
	versions = get_resume_versions(run_id)
	comparisons = [
		{"previous": versions[index - 1], "current": version}
		for index, version in enumerate(versions)
		if index > 0
	]
	return {"run": context["run"], "versions": versions, "comparisons": comparisons}


@app.get("/optimization-runs/{run_id}/resume.pdf")
def optimization_resume_pdf(run_id: int) -> FileResponse:
	context = get_optimization_context(run_id)
	if context is None or context["resume"] is None:
		raise HTTPException(status_code=404, detail="Resume version not found")
	rendered_path = context["resume"].get("rendered_file_path")
	if not rendered_path:
		raise HTTPException(status_code=404, detail="Generated PDF not found")
	path = Path(rendered_path).resolve()
	try:
		path.relative_to(GENERATED_RESUMES_DIR.resolve())
	except ValueError as error:
		raise HTTPException(status_code=404, detail="Generated PDF not found") from error
	if not path.is_file():
		raise HTTPException(status_code=404, detail="Generated PDF not found")
	return FileResponse(path, media_type="application/pdf", filename=f"resume-run-{run_id}.pdf")


@app.post("/resumes", status_code=201)
def upload_resume(file: UploadFile = File(...)) -> dict[str, Any]:
	if file.content_type != "application/pdf" or not file.filename or not file.filename.lower().endswith(".pdf"):
		raise HTTPException(status_code=415, detail="Only PDF resume files are supported")

	stored_path = ORIGINAL_RESUMES_DIR / f"{uuid4().hex}.pdf"
	try:
		with stored_path.open("wb") as destination:
			total_bytes = 0
			while chunk := file.file.read(1024 * 1024):
				total_bytes += len(chunk)
				if total_bytes > MAX_UPLOAD_BYTES:
					raise HTTPException(status_code=413, detail="Resume must be 10 MB or smaller")
				destination.write(chunk)
		resume = ingest_resume(stored_path, original_file_path=str(stored_path))
	except HTTPException:
		stored_path.unlink(missing_ok=True)
		raise
	except Exception as error:
		stored_path.unlink(missing_ok=True)
		raise HTTPException(status_code=422, detail=f"Could not parse resume PDF: {error}") from error
	finally:
		file.file.close()

	return {"resumeId": str(resume["resume_id"]), "resume": resume}


@app.get("/jobs/{job_id}/match")
def match_job(job_id: int, resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	job = get_job(job_id)
	resume_record = get_latest_resume() if resume_id is None else None
	if resume_id is not None:
		resume_record = get_resume(resume_id)
	if job is None:
		raise HTTPException(status_code=404, detail="Job not found")
	if resume_record is None:
		raise HTTPException(status_code=404, detail="Resume not found")
	resume = get_full_resume(resume_record["id"])
	try:
		job_ir = parse_job(job)
		report = evaluate_resume(resume_for_evaluator(resume), job_ir, BedrockNovaClient())
	except BedrockClientError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error
	run = create_optimization_run(resume_record["id"], job_id, max_iterations=3)
	version = create_resume_version(run["id"], resume_record.get("resume_json") or resume)
	evaluation = save_evaluation(run["id"], version["id"], 0, report.ats_score, report.model_dump())
	requirements = match_requirements_to_frontend(
		matched_skills=report.matched_skills,
		missing_skills=report.missing_skills,
		resume_skills=resume.get("skills") or [],
	)
	return {
		"jobId": str(job_id),
		"jobTitle": job["job_title"],
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"verdict": verdict_for_score(report.ats_score),
		"verdictLabel": "Strong match" if report.ats_score >= 70 else "Review gaps",
		"score": report.ats_score,
		"agents": [{"name": "ATS evaluator", "ok": True, "detail": "Evaluation persisted locally"}],
		"requirements": requirements,
		"workPass": WORK_PASS_STUB,
		"evaluationId": evaluation["id"],
		"evaluation": report.model_dump(),
	}


@app.post("/jobs/{job_id}/optimize")
def optimize_job(job_id: int, resume_id: int = Query(...), max_iterations: int = Query(default=3, ge=1, le=10), min_score_improvement: float = Query(default=2, ge=0), target_score: float = Query(default=85, ge=0, le=100)) -> dict[str, Any]:
	try:
		result = optimize_resume(resume_id, job_id, BedrockNovaClient(), max_iterations, min_score_improvement, target_score)
		if result["run"]["status"] == "completed":
			result["resumePdfUrl"] = f"/optimization-runs/{result['run']['id']}/resume.pdf"
		return result
	except ValueError as error:
		raise HTTPException(status_code=404, detail=str(error)) from error
	except BedrockClientError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/jobs/{job_id}/actions")
def job_actions(job_id: int, resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	job = get_job(job_id)
	if job is None:
		raise HTTPException(status_code=404, detail="Job not found")
	resume_summary = get_latest_resume() if resume_id is None else get_resume(resume_id)
	if resume_summary is None:
		raise HTTPException(status_code=404, detail="Resume not found")
	resolved_resume_id = resume_summary["id"]
	resume_record = get_full_resume(resolved_resume_id)
	if resume_record is None:
		raise HTTPException(status_code=404, detail="Resume not found")

	try:
		result = optimize_resume(resolved_resume_id, job_id, BedrockNovaClient(), max_iterations=2, min_score_improvement=1, target_score=90)
	except ValueError as error:
		raise HTTPException(status_code=404, detail=str(error)) from error
	except BedrockClientError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error

	evaluation = result.get("evaluation") or {}
	matched = evaluation.get("matched_skills") or []
	missing = evaluation.get("missing_skills") or []

	authoritative = resume_record.get("resume", {}).get("resume_json") or resume_record
	run_status = (result.get("run") or {}).get("status")
	if run_status == "completed":
		final_resume = result.get("resume") or authoritative
		run_id = (result.get("run") or {}).get("id")
		diffs = build_resume_diffs(authoritative, final_resume, run_id)
		if not diffs:
			diffs = demo_tailor_fallback(job_id, resolved_resume_id) or []
		blocked = None
	else:
		diffs = []
		blocked = build_blocked_claim(result.get("validation"))

	return {
		"jobId": str(job_id),
		"jobTitle": job["job_title"],
		"company": job.get("company_name") or "",
		"met": len(matched),
		"total": len(matched) + len(missing),
		"diffs": diffs,
		"blocked": blocked,
		"skills": build_skill_gaps(missing, job_id, get_all_jobs()),
	}