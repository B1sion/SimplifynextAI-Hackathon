import os
from pathlib import Path
from typing import Any

from src.Tools.education_project_tools import add_education, add_project
from src.Tools.person_tools import create_person
from src.Tools.resume_tools import create_resume, get_full_resume
from src.Tools.skill_tools import add_skill_to_resume, create_skill
from src.Tools.work_experience_tools import add_experience_bullet, add_work_experience
from src.agents.resume_parser import extract_pdf_text, parse_resume, parse_resume_with_agent

def ingest_resume(file_path: Path, original_file_path: str | None = None) -> dict[str, Any] | None:
    text = extract_pdf_text(file_path)
    parsed = parse_resume_with_agent(text) if os.environ.get("AGENTCORE_RUNTIME_ARN") else parse_resume(text)
    person_id = create_person(
        parsed["name"],
        email=parsed["email"],
        phone=parsed["phone"],
        linkedin_url=parsed["linkedin_url"],
        github_url=parsed["github_url"],
        portfolio_url=parsed.get("portfolio_url"),
    )
    resume_id = create_resume(
        person_id,
        file_path.stem,
        original_file_path=original_file_path,
        raw_text=parsed["raw_text"],
        resume_json=parsed,
    )

    for experience in parsed["work_experience"]:
        bullets = experience.get("bullets", [])
        experience_data = {key: value for key, value in experience.items() if key != "bullets"}
        experience_id = add_work_experience(resume_id, **experience_data)
        for bullet_order, bullet in enumerate(bullets):
            add_experience_bullet(experience_id, bullet, bullet_order=bullet_order)
    for education in parsed["education"]:
        add_education(resume_id, **education)
    for project in parsed["projects"]:
        project_data = {key: value for key, value in project.items() if key not in {"bullets"}}
        bullets = project.get("bullets") or []
        if bullets:
            project_data["description"] = "\n".join(filter(None, [project_data.get("description"), *bullets]))
        add_project(resume_id, **project_data)
    for skill_name in parsed["skills"]:
        skill_id = create_skill(skill_name)
        add_skill_to_resume(resume_id, skill_id, source="explicit", evidence=skill_name)

    return get_full_resume(resume_id)
