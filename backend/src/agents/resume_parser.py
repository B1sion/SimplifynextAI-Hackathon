import re
from pathlib import Path

from pypdf import PdfReader


SECTION_NAMES = {
    "experience": {"experience", "work experience", "work history", "employment"},
    "education": {"education", "academic background"},
    "projects": {"projects", "personal projects"},
    "skills": {"skills", "technical skills", "core skills"},
}
RESUME_READER_PROMPT_PATH = Path(__file__).parent / "resume_agents" / "Resume_reader.md"


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _section_lines(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {name: [] for name in SECTION_NAMES}
    current: str | None = None
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split()).strip()
        if not line:
            continue
        normalized = line.lower().rstrip(":")
        matched = next((name for name, headings in SECTION_NAMES.items() if normalized in headings), None)
        if matched:
            current = matched
        elif current:
            sections[current].append(line)
    return sections


def _first_name(text: str) -> str:
    for line in text.splitlines():
        candidate = " ".join(line.split()).strip()
        if candidate and not re.search(r"@|https?://|\+?\d[\d ()-]{6,}", candidate):
            if len(candidate.split()) <= 5 and not candidate.endswith(":"):
                return candidate
    return "Unknown"


def _parse_experience(lines: list[str]) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    for index, line in enumerate(lines):
        if " | " in line:
            job_title, company_name = [part.strip() for part in line.split(" | ", 1)]
            entries.append({"company_name": company_name, "job_title": job_title, "description": None, "experience_order": index})
        elif " - " in line and len(line.split(" - ", 1)[0].split()) <= 8:
            job_title, company_name = [part.strip() for part in line.split(" - ", 1)]
            entries.append({"company_name": company_name, "job_title": job_title, "description": None, "experience_order": index})
        elif entries:
            description = entries[-1]["description"]
            entries[-1]["description"] = f"{description}\n{line}" if description else line
    return entries


def _parse_education(lines: list[str]) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    for index, line in enumerate(lines):
        parts = [part.strip() for part in re.split(r"\s+\|\s+|\s+[-–]\s+", line, maxsplit=1)]
        if len(parts) == 2:
            institution, degree = parts
        else:
            institution, degree = line, None
        entries.append({"institution": institution, "degree": degree, "education_order": index})
    return entries


def _parse_projects(lines: list[str]) -> list[dict[str, str | None]]:
    return [
        {"project_name": line.split(" - ", 1)[0].strip(), "description": line.split(" - ", 1)[1].strip() if " - " in line else None, "project_order": index}
        for index, line in enumerate(lines)
    ]


def parse_resume(text: str) -> dict:
    sections = _section_lines(text)
    email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    phone_match = re.search(r"(?:\+?\d[\d ()-]{7,}\d)", text)
    urls = re.findall(r"https?://\S+", text)
    skills = [skill.strip() for line in sections["skills"] for skill in re.split(r",|\||•", line) if skill.strip()]
    return {
        "name": _first_name(text),
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "linkedin_url": next((url for url in urls if "linkedin.com" in url.lower()), None),
        "github_url": next((url for url in urls if "github.com" in url.lower()), None),
        "raw_text": text,
        "work_experience": _parse_experience(sections["experience"]),
        "education": _parse_education(sections["education"]),
        "projects": _parse_projects(sections["projects"]),
        "skills": skills,
    }


def parse_resume_with_agent(text: str) -> dict:
    """Ask AgentCore to convert text into resume JSON."""
    from src.agents.resume_agents.agentcore_client import AgentCoreClient

    parsed = AgentCoreClient().parse_resume(text)
    return {**parsed, "raw_text": text}
