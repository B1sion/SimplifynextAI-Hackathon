from typing import Any


DISCOVER_VERDICT_LABELS = {"v": "Can apply", "c": "Might not qualify", "b": "Cannot apply"}

WORK_PASS_STUB: dict[str, Any] = {
	"points": 0,
	"needed": 40,
	"summary": "Work pass scoring is not available yet.",
}

COMPASS_STUB_CRITERIA: list[dict[str, Any]] = [
	{"code": "C1", "name": "Salary", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C2", "name": "Qualifications", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C3", "name": "Diversity", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C4", "name": "Support for local employment", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C5", "name": "Skills bonus", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C6", "name": "Strategic economic priorities bonus", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
]


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


def compass_stub_report(job: dict[str, Any]) -> dict[str, Any]:
	return {
		"jobId": str(job["id"]),
		"jobTitle": job.get("job_title") or "",
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"needed": WORK_PASS_STUB["needed"],
		"criteria": COMPASS_STUB_CRITERIA,
		"closingTheGap": "Work pass scoring is not implemented yet.",
		"disclaimer": "This is a placeholder. COMPASS scoring has not been implemented.",
	}
