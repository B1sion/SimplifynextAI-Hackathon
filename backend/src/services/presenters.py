from typing import Any


DISCOVER_VERDICT_LABELS = {"v": "Can apply", "c": "Might not qualify", "b": "Cannot apply"}

WORK_PASS_STUB: dict[str, Any] = {
	"points": 0,
	"needed": 40,
	"summary": "Work pass scoring is not available yet.",
}

COMPASS_NEEDED_POINTS = 40

# Approximate monthly salary bands (SGD) used only to rank a job's own listed
# salary relative to itself — not the real MOM COMPASS percentile tables,
# which require sector/age salary distribution data this app does not have.
_COMPASS_SALARY_STRONG_BAND = 3000
_COMPASS_SALARY_BASE_BAND = 2000

_COMPASS_NO_DATA_CRITERIA = (
	("C3", "Diversity", "employer nationality-mix"),
	("C4", "Support for local employment", "local PMET employment share"),
	("C6", "Strategic economic priorities bonus", "strategic economic priority partnership"),
)


def _compass_salary_criterion(job: dict[str, Any]) -> dict[str, Any]:
	salary_min = job.get("salary_min")
	salary_max = job.get("salary_max")
	if salary_min and salary_max:
		midpoint = (salary_min + salary_max) / 2
	elif salary_min or salary_max:
		midpoint = salary_min or salary_max
	else:
		return {"code": "C1", "name": "Salary", "points": 0, "verdict": "b", "detail": "This job listing has no salary data to score against."}
	if midpoint >= _COMPASS_SALARY_STRONG_BAND:
		return {"code": "C1", "name": "Salary", "points": 20, "verdict": "v", "detail": f"Listed salary (~S${midpoint:,.0f}/mo midpoint) clears the higher salary band."}
	if midpoint >= _COMPASS_SALARY_BASE_BAND:
		return {"code": "C1", "name": "Salary", "points": 10, "verdict": "c", "detail": f"Listed salary (~S${midpoint:,.0f}/mo midpoint) clears the base salary band."}
	return {"code": "C1", "name": "Salary", "points": 0, "verdict": "b", "detail": f"Listed salary (~S${midpoint:,.0f}/mo midpoint) falls below the qualifying band."}


def _compass_qualifications_criterion(education: list[dict[str, Any]]) -> dict[str, Any]:
	degree_text = " ".join(str(entry.get("degree") or "") for entry in education).casefold()
	if any(keyword in degree_text for keyword in ("phd", "doctor")):
		return {"code": "C2", "name": "Qualifications", "points": 20, "verdict": "v", "detail": "Doctoral qualification found on the resume."}
	if any(keyword in degree_text for keyword in ("master", "msc", "mba", "m.a.", "m.eng")):
		return {"code": "C2", "name": "Qualifications", "points": 20, "verdict": "v", "detail": "Postgraduate qualification found on the resume."}
	if any(keyword in degree_text for keyword in ("bachelor", "b.b.a", "b.a.", "b.s.", "bsc", "b.eng", "undergraduate")):
		return {"code": "C2", "name": "Qualifications", "points": 10, "verdict": "c", "detail": "Undergraduate degree found on the resume."}
	return {"code": "C2", "name": "Qualifications", "points": 0, "verdict": "b", "detail": "No recognised post-secondary qualification found on the resume."}


def _compass_skills_criterion(job: dict[str, Any], skills: list[dict[str, Any]]) -> dict[str, Any]:
	job_text = (job.get("job_description") or "").casefold()
	resume_skill_names = [str(skill.get("name") or "") for skill in skills if skill.get("name")]
	matched = [name for name in resume_skill_names if name.casefold() in job_text]
	if not resume_skill_names:
		return {"code": "C5", "name": "Skills bonus", "points": 0, "verdict": "b", "detail": "No resume skills on file to compare against this job's requirements."}
	ratio = len(matched) / len(resume_skill_names)
	detail = f"{len(matched)} of {len(resume_skill_names)} resume skills appear directly in this job's requirements."
	if ratio >= 0.5:
		return {"code": "C5", "name": "Skills bonus", "points": 10, "verdict": "v", "detail": detail}
	if ratio > 0:
		return {"code": "C5", "name": "Skills bonus", "points": 5, "verdict": "c", "detail": detail}
	return {"code": "C5", "name": "Skills bonus", "points": 0, "verdict": "b", "detail": detail}


def compute_compass_report(job: dict[str, Any], resume_full: dict[str, Any] | None) -> dict[str, Any]:
	"""Estimate a COMPASS-style score from data this MVP actually has (job salary
	band, resume qualification level, and direct skill-keyword overlap). This is
	NOT the official MOM COMPASS algorithm — criteria that require employer-level
	data we don't have (nationality mix, local PMET share, strategic partnerships)
	are honestly scored 0 with an explanation rather than guessed.
	"""
	education = (resume_full or {}).get("education") or []
	skills = (resume_full or {}).get("skills") or []

	criteria = [
		_compass_salary_criterion(job),
		_compass_qualifications_criterion(education),
	]
	criteria.extend(
		{"code": code, "name": name, "points": 0, "verdict": "b", "detail": f"No {label} data is available for this job listing to score this criterion."}
		for code, name, label in _COMPASS_NO_DATA_CRITERIA[:2]
	)
	criteria.append(_compass_skills_criterion(job, skills))
	criteria.append(
		{"code": "C6", "name": "Strategic economic priorities bonus", "points": 0, "verdict": "b", "detail": f"No {_COMPASS_NO_DATA_CRITERIA[2][2]} data is available for this job listing to score this criterion."}
	)
	# Restore canonical C1..C6 ordering (criteria was built C1, C2, C3, C4, C5, C6).
	criteria.sort(key=lambda item: item["code"])

	total = sum(criterion["points"] for criterion in criteria)
	gaps = [criterion["detail"] for criterion in criteria if criterion["points"] == 0]
	closing_the_gap = " ".join(gaps) if gaps else "This role already clears the estimated COMPASS threshold based on the data available."
	disclaimer = (
		"Estimated from the job listing and resume data this MVP actually has (salary band, qualification "
		"level, and direct skill-keyword overlap) — not the official MOM COMPASS algorithm. Diversity, local-"
		"employment share, and strategic-priority bonuses require employer-level data this app does not collect, "
		"so those three criteria are always scored 0 rather than guessed."
	)
	return {
		"jobId": str(job["id"]),
		"jobTitle": job.get("job_title") or "",
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"needed": COMPASS_NEEDED_POINTS,
		"criteria": criteria,
		"closingTheGap": closing_the_gap,
		"disclaimer": disclaimer,
	}


def verdict_for_score(score: float) -> str:
	if score >= 70:
		return "v"
	if score >= 50:
		return "c"
	return "b"


def job_to_frontend(job: dict[str, Any], score: float | None) -> dict[str, Any]:
	resolved_score = score if score is not None else 0
	verdict = verdict_for_score(resolved_score)
	return {
		"id": str(job["id"]),
		"title": job.get("job_title") or "",
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"score": int(resolved_score / 10 + 0.5),
		"verdict": verdict,
		"verdictLabel": DISCOVER_VERDICT_LABELS[verdict],
	}


def facts_to_groups(full_resume: dict[str, Any]) -> list[dict[str, Any]]:
	groups: list[dict[str, Any]] = []

	skills = full_resume.get("skills") or []
	if skills:
		groups.append(
			{
				"group": "Skills",
				"items": [
					{
						"value": skill.get("name") or "",
						"source": skill.get("evidence") or "No evidence captured",
						"location": f"Resume · {skill.get('category') or 'Skills'}",
					}
					for skill in skills
				],
			}
		)

	experiences = full_resume.get("work_experience") or []
	experience_items = [
		{
			"value": bullet,
			"source": bullet,
			"location": f"{experience.get('company_name') or ''} · {experience.get('job_title') or ''}",
		}
		for experience in experiences
		for bullet in (experience.get("bullets") or [])
	]
	if experience_items:
		groups.append({"group": "Work Experience", "items": experience_items})

	education = full_resume.get("education") or []
	if education:
		groups.append(
			{
				"group": "Education",
				"items": [
					{
						"value": f"{entry.get('degree') or ''} in {entry.get('field_of_study') or ''}".strip(" in ") or entry.get("institution") or "",
						"source": entry.get("description") or entry.get("institution") or "",
						"location": entry.get("institution") or "Education",
					}
					for entry in education
				],
			}
		)

	projects = full_resume.get("projects") or []
	if projects:
		groups.append(
			{
				"group": "Projects",
				"items": [
					{
						"value": project.get("project_name") or "",
						"source": project.get("description") or project.get("project_name") or "",
						"location": "Projects",
					}
					for project in projects
				],
			}
		)

	return groups


def find_skill_evidence(resume_skills: list[dict[str, Any]], skill_name: str) -> str:
	for skill in resume_skills:
		if str(skill.get("name", "")).casefold() == skill_name.casefold():
			return skill.get("evidence") or "Found in resume"
	return "Found in resume"


def match_requirements_to_frontend(
	matched_skills: list[str], missing_skills: list[str], resume_skills: list[dict[str, Any]]
) -> list[dict[str, Any]]:
	requirements: list[dict[str, Any]] = [
		{
			"met": True,
			"text": skill,
			"evidence": find_skill_evidence(resume_skills, skill),
			"location": "Resume",
		}
		for skill in matched_skills
	]
	requirements.extend(
		{"met": False, "text": skill, "note": "Not found in the resume"} for skill in missing_skills
	)
	return requirements
