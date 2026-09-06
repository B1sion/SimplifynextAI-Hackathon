from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from database.database import initialize_database
from src.Tools.evaluation_tools import save_evaluation
from src.Tools.job_tools import get_job
from src.Tools.optimization_tools import create_optimization_run, create_resume_version
from src.Tools.resume_tools import get_full_resume, get_latest_resume
from src.agents.resume_agents.agentcore_client import AgentCoreClient, AgentCoreError
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job
from src.agents.resume_ingestion import ingest_resume
from src.services.optimization_engine import optimize_resume


ROOT_DIR = Path(__file__).resolve().parents[2]
ORIGINAL_RESUMES_DIR = ROOT_DIR / "storage" / "original_resumes"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(title="Simplify Resume API")


@app.on_event("startup")
def startup() -> None:
	initialize_database()
	ORIGINAL_RESUMES_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@app.post("/resumes", status_code=201)
def upload_resume(file: UploadFile = File(...)) -> dict:
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
def match_job(job_id: int, resume_id: int | None = Query(default=None)) -> dict:
	job = get_job(job_id)
	resume_record = get_latest_resume() if resume_id is None else None
	if resume_id is not None:
		from src.Tools.resume_tools import get_resume

		resume_record = get_resume(resume_id)
	if job is None:
		raise HTTPException(status_code=404, detail="Job not found")
	if resume_record is None:
		raise HTTPException(status_code=404, detail="Resume not found")
	resume = get_full_resume(resume_record["id"])
	try:
		job_ir = parse_job(job)
		report = evaluate_resume(resume, job_ir, AgentCoreClient())
	except AgentCoreError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error
	run = create_optimization_run(resume_record["id"], job_id, max_iterations=3)
	version = create_resume_version(run["id"], resume_record.get("resume_json") or resume)
	evaluation = save_evaluation(run["id"], version["id"], 0, report.overall_score, report.model_dump())
	requirements = [
		{"met": True, "text": item, "evidence": ", ".join(report.supporting_resume_evidence.get(item, [])), "location": "Resume"}
		for item in report.matched_requirements
	]
	requirements.extend({"met": False, "text": item, "note": "Not found in the resume"} for item in report.missing_requirements)
	return {
		"jobId": str(job_id),
		"jobTitle": job["job_title"],
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"verdict": "v" if report.overall_score >= 70 else "c" if report.overall_score >= 50 else "b",
		"verdictLabel": "Strong match" if report.overall_score >= 70 else "Review gaps",
		"score": report.overall_score,
		"agents": [{"name": "ATS evaluator", "ok": True, "detail": "Evaluation persisted locally"}],
		"requirements": requirements,
		"evaluationId": evaluation["id"],
		"evaluation": report.model_dump(),
	}


@app.post("/jobs/{job_id}/optimize")
def optimize_job(job_id: int, resume_id: int = Query(...), max_iterations: int = Query(default=3, ge=1, le=10), min_score_improvement: float = Query(default=2, ge=0), target_score: float = Query(default=85, ge=0, le=100)) -> dict:
	try:
		return optimize_resume(resume_id, job_id, AgentCoreClient(), max_iterations, min_score_improvement, target_score)
	except ValueError as error:
		raise HTTPException(status_code=404, detail=str(error)) from error
	except AgentCoreError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error