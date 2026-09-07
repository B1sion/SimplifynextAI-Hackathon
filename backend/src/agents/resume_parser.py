import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


SECTION_NAMES = {
    "experience": {"experience", "work experience", "work history", "employment"},
    "education": {"education", "academic background"},
    "projects": {"projects", "personal projects"},
    "leadership": {"leadership & activities", "leadership and activities", "activities"},
    "skills": {"skills", "skills & interests", "technical skills", "core skills"},
}
SECTION_ALIASES = {
    "education experience": "experience",
    "other experience": "experience",
    "other experiences": "experience",
}
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_RANGE_RE = re.compile(
    rf"\s+(?P<start>{MONTH}\s*\d{{0,4}})\s*[-–—?]\s*(?P<end>(?:{MONTH}|Present)(?:\s+\d{{4}})?)$",
    re.IGNORECASE,
)
INLINE_DATE_RANGE_RE = re.compile(
    rf"(?P<start>{MONTH}\s*\d{{0,4}})\s*[-–—?]\s*(?P<end>(?:{MONTH}|Present)(?:\s+\d{{4}})?)$",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\s+(?P<year>\d{4})$")
SINGLE_DATE_RE = re.compile(rf"\s+(?P<date>{MONTH}\s+\d{{4}})$", re.IGNORECASE)
BULLET_RE = re.compile(r"^(?:[●•▪◦*-])\s*")
RESUME_READER_PROMPT_PATH = Path(__file__).parent / "resume_agents" / "Resume_reader.md"


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages: list[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text(extraction_mode="layout") or ""
        except (TypeError, ValueError):
            page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n".join(pages).strip()


def _section_lines(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {name: [] for name in SECTION_NAMES}
    current: str | None = None
    for raw_line in text.splitlines():
        line = " ".join(raw_line.replace("\u200b", "").replace("\ufeff", "").split()).strip()
        if not line:
            continue
        normalized = line.lower().rstrip(":")
        matched = SECTION_ALIASES.get(normalized) or next((name for name, headings in SECTION_NAMES.items() if normalized in headings), None)
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


def _parse_experience(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        inline_date = INLINE_DATE_RANGE_RE.search(line)
        if inline_date:
            header = line[:inline_date.start()].strip(" -–—")
            if " — " in header:
                job_title, company_name = [part.strip() for part in header.split(" — ", 1)]
            elif " | " in header:
                job_title, company_name = [part.strip() for part in header.split(" | ", 1)]
            else:
                job_title, company_name = None, header
            entries.append({
                "company_name": company_name,
                "job_title": job_title,
                "start_date": inline_date.group("start").strip(),
                "end_date": inline_date.group("end").strip(),
                "description": None,
                "bullets": [],
                "experience_order": index,
            })
        elif " | " in line:
            job_title, company_name = [part.strip() for part in line.split(" | ", 1)]
            entries.append({"company_name": company_name, "job_title": job_title, "description": None, "bullets": [], "experience_order": index})
        else:
            date_match = DATE_RANGE_RE.search(line)
            if date_match:
                company_name = line[:date_match.start()].strip()
                entries.append({
                    "company_name": company_name,
                    "job_title": None,
                    "start_date": date_match.group("start").strip(),
                    "end_date": date_match.group("end").strip(),
                    "description": None,
                    "bullets": [],
                    "experience_order": index,
                })
            elif entries and entries[-1]["job_title"] is None:
                entries[-1]["job_title"] = line
            elif entries:
                bullet = BULLET_RE.sub("", line).strip()
                if bullet != line and isinstance(entries[-1].get("bullets"), list):
                    entries[-1]["bullets"].append(bullet)
                    line = bullet
                elif isinstance(entries[-1].get("bullets"), list) and entries[-1]["bullets"]:
                    entries[-1]["bullets"][-1] = f"{entries[-1]['bullets'][-1]} {line}".strip()
                description = entries[-1]["description"]
                entries[-1]["description"] = f"{description}\n{line}" if description else line
    return entries


def _parse_education(lines: list[str]) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    for line in lines:
        if line.lower().startswith("relevant coursework:") and entries:
            coursework = line
            if " | " in coursework:
                coursework, grade = coursework.split(" | ", 1)
                entries[-1]["grade"] = grade.removeprefix("CAP:").removeprefix("GPA:").strip()
            entries[-1]["description"] = coursework
            continue
        inline_date = INLINE_DATE_RANGE_RE.search(line)
        if inline_date:
            header = line[:inline_date.start()].strip(" -–—")
            if " — " in header:
                institution, degree = [part.strip() for part in header.split(" — ", 1)]
            else:
                institution, degree = header, None
            entries.append({
                "institution": institution,
                "degree": degree,
                "start_date": inline_date.group("start").strip(),
                "end_date": inline_date.group("end").strip(),
                "description": None,
                "education_order": len(entries),
            })
            continue
        date_match = DATE_RANGE_RE.search(line)
        if " — " in line and not date_match:
            institution, degree = [part.strip() for part in line.split(" — ", 1)]
            entries.append({"institution": institution, "degree": degree, "description": None, "education_order": len(entries)})
        elif " | " in line and not date_match:
            institution, degree = [part.strip() for part in line.split(" | ", 1)]
            entries.append({"institution": institution, "degree": degree, "description": None, "education_order": len(entries)})
        elif date_match:
            institution = line[:date_match.start()].strip()
            entries.append({
                "institution": institution,
                "degree": None,
                "start_date": date_match.group("start").strip(),
                "end_date": date_match.group("end").strip(),
                "description": None,
                "education_order": len(entries),
            })
        elif entries and re.search(r"(?:CAP|GPA)\s*:", line, re.IGNORECASE):
            entries[-1]["grade"] = re.search(r"(?:CAP|GPA)\s*:\s*(.+)$", line, re.IGNORECASE).group(1)
        elif entries and entries[-1]["degree"] is None:
            entries[-1]["degree"] = line
        elif entries:
            description = entries[-1]["description"]
            entries[-1]["description"] = f"{description}\n{line}" if description else line
        else:
            entries.append({"institution": line, "degree": None, "description": None, "education_order": len(entries)})
    return entries


def _parse_projects(lines: list[str]) -> list[dict[str, str | None]]:
    entries: list[dict[str, Any]] = []
    for line in lines:
        date_match = INLINE_DATE_RANGE_RE.search(line)
        if date_match:
            header = line[:date_match.start()].strip(" -–—")
            entries.append({
                "project_name": header,
                "start_date": date_match.group("start"),
                "end_date": date_match.group("end"),
                "description": None,
                "bullets": [],
                "project_order": len(entries),
            })
        elif (single_date := SINGLE_DATE_RE.search(line)):
            entries.append({
                "project_name": line[:single_date.start()].strip(" -–—") or line,
                "start_date": single_date.group("date").strip(),
                "end_date": None,
                "description": None,
                "bullets": [],
                "project_order": len(entries),
            })
        elif (year_match := YEAR_RE.search(line)):
            entries.append({
                "project_name": line[:year_match.start()].strip(" -–—") or line,
                "start_date": year_match.group("year"),
                "end_date": None,
                "description": None,
                "bullets": [],
                "project_order": len(entries),
            })
        elif entries and BULLET_RE.match(line):
            entries[-1].setdefault("bullets", []).append(BULLET_RE.sub("", line).strip())
        elif entries:
            bullets = entries[-1].setdefault("bullets", [])
            if bullets:
                bullets[-1] = f"{bullets[-1]} {line}".strip()
            else:
                entries[-1]["description"] = f"{entries[-1].get('description') or ''} {line}".strip()
        else:
            parts = line.split(" - ", 1)
            entries.append({"project_name": parts[0].strip(), "description": parts[1].strip() if len(parts) > 1 else None, "project_order": len(entries)})
    return entries


def parse_resume(text: str) -> dict[str, Any]:
    sections = _section_lines(text)
    email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    phone_match = re.search(r"(?:\+?\d[\d ()-]{7,}\d)", text)
    urls = [url.rstrip(".,;)") for url in re.findall(r"(?:(?:https?://|www\.)\S+|(?:linkedin|github)\.com/\S+)", text, re.IGNORECASE)]
    other_urls = [url for url in urls if "linkedin.com" not in url.lower() and "github.com" not in url.lower()]
    skills: list[str] = []
    for line in sections["skills"]:
        if line.startswith("(") and skills:
            skills[-1] = f"{skills[-1]} {line}".strip()
        elif re.match(r"(?:technical|languages|interests)\s*:", line, re.IGNORECASE):
            skills.append(line)
        else:
            skills.extend(skill.strip() for skill in re.split(r",|\||•", line) if skill.strip())
    return {
        "name": _first_name(text),
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "linkedin_url": next((url for url in urls if "linkedin.com" in url.lower()), None),
        "github_url": next((url for url in urls if "github.com" in url.lower()), None),
        "portfolio_url": next((url for url in other_urls if url.lower().startswith(("http", "www."))), None),
        "other_urls": other_urls,
        "raw_text": text,
        "work_experience": _parse_experience(sections["experience"]),
        "education": _parse_education(sections["education"]),
        "projects": _parse_projects(sections["leadership"] + sections["projects"]),
        "skills": skills,
    }


def parse_resume_with_agent(text: str) -> dict[str, Any]:
    """Ask AgentCore to convert extracted text into resume JSON."""
    from src.agents.resume_agents.agentcore_client import AgentCoreClient

    parsed = AgentCoreClient().parse_resume(text)
    return {**parsed, "raw_text": text}


def parse_resume_pdf_with_agent(pdf_bytes: bytes, filename: str = "resume.pdf", raw_text: str | None = None) -> dict[str, Any]:
    """Ask AgentCore to read the original PDF while retaining searchable text."""
    from src.agents.resume_agents.agentcore_client import AgentCoreClient

    parsed = AgentCoreClient().parse_resume_pdf(pdf_bytes, filename=filename)
    return {**parsed, "raw_text": raw_text or ""}
