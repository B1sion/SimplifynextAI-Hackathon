from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from database.database import initialize_database
from src.agents.resume_ingestion import ingest_resume


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