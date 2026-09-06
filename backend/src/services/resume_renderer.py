from html import escape
from pathlib import Path
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


GENERATED_RESUMES_DIR = Path(__file__).resolve().parents[2] / "storage" / "generated_resumes"


def _value(value: Any) -> str:
    return escape(str(value)) if value is not None else ""


def _paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_value(text).replace("\n", "<br/>"), style)


def _clean_bullet(text: Any) -> str:
    value = str(text or "").strip()
    return re.sub(r"^(?:[●•▪◦*-]|\u2022)\s*", "", value).strip()


def _date_range(item: dict[str, Any]) -> str:
    start = item.get("start_date") or item.get("startDate") or ""
    end = item.get("end_date") or item.get("endDate") or ""
    return " - ".join(part for part in (start, end) if part)


def _add_section(story: list[Any], title: str, section_style: ParagraphStyle) -> None:
    story.append(Spacer(1, 0.1 * inch))
    rule = HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#222222"), spaceBefore=4)
    section = Table([[Paragraph(title.upper(), section_style), rule]], colWidths=[1.2 * inch, 5.8 * inch])
    section.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(section)


def _add_entry(
    story: list[Any],
    heading: str,
    date_range: str,
    details: list[Any],
    heading_style: ParagraphStyle,
    metadata_style: ParagraphStyle,
) -> None:
    entry: list[Any] = []
    if heading or date_range:
        header = Table(
            [[_paragraph(heading, heading_style), _paragraph(date_range, metadata_style)]],
            colWidths=[5.25 * inch, 1.75 * inch],
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        entry.append(header)
    entry.extend(details)
    story.append(KeepTogether(entry))


def render_resume_pdf(
    resume: dict[str, Any],
    run_id: int,
    version_number: int,
    output_dir: Path | None = None,
) -> Path:
    destination = output_dir or GENERATED_RESUMES_DIR
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / f"resume_run_{run_id}_version_{version_number}.pdf"

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        spaceAfter=6,
    )
    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#444444"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "ResumeSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#222222"),
        borderWidth=0,
        borderPadding=0,
        spaceAfter=5,
        keepWithNext=True,
    )
    heading_style = ParagraphStyle(
        "ResumeEntry",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        spaceAfter=1,
        keepWithNext=True,
    )
    metadata_style = ParagraphStyle(
        "ResumeMetadata",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
        alignment=TA_RIGHT,
        spaceAfter=1,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=body_style,
        leftIndent=13,
        firstLineIndent=-7,
        bulletIndent=0,
        spaceAfter=2,
    )

    story: list[Any] = []
    story.append(Paragraph(_value(resume.get("name") or "Resume"), name_style))
    contacts = [
        resume.get("email"),
        resume.get("phone"),
        resume.get("linkedin_url"),
        resume.get("github_url"),
    ]
    contact_text = " | ".join(_value(value) for value in contacts if value)
    if contact_text:
        story.append(Paragraph(contact_text, contact_style))

    if resume.get("summary"):
        _add_section(story, "Summary", section_style)
        story.append(_paragraph(resume["summary"], body_style))

    education = resume.get("education") or []
    if education:
        _add_section(story, "Education", section_style)
        for item in education:
            institution = item.get("institution") or ""
            degree = item.get("degree") or item.get("studyType") or ""
            heading = " | ".join(part for part in (institution, degree) if part)
            details = []
            if item.get("description"):
                details.append(_paragraph(item["description"], body_style))
            _add_entry(story, heading, _date_range(item), details, heading_style, metadata_style)

    work = resume.get("work_experience") or resume.get("work") or []
    if work:
        _add_section(story, "Experience", section_style)
        for item in work:
            company = item.get("company_name") or item.get("name") or ""
            title = item.get("job_title") or item.get("position") or ""
            heading = " | ".join(part for part in (company, title) if part)
            details = []
            bullets = item.get("bullets") or item.get("highlights") or []
            if bullets:
                for bullet in bullets:
                    details.append(Paragraph(_value(_clean_bullet(bullet)), bullet_style, bulletText="•"))
            elif item.get("description"):
                details.append(_paragraph(item["description"], body_style))
            _add_entry(story, heading, _date_range(item), details, heading_style, metadata_style)

    projects = resume.get("projects") or []
    if projects:
        _add_section(story, "Projects", section_style)
        for item in projects:
            name = item.get("project_name") or item.get("name") or ""
            details = []
            if item.get("description"):
                details.append(_paragraph(item["description"], body_style))
            for bullet in item.get("bullets") or item.get("highlights") or []:
                details.append(Paragraph(_value(_clean_bullet(bullet)), bullet_style, bulletText="•"))
            _add_entry(story, name, _date_range(item), details, heading_style, metadata_style)

    skills = resume.get("skills") or []
    if skills:
        _add_section(story, "Skills", section_style)
        skill_names = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_names.append(skill.get("name") or skill.get("skill") or "")
            else:
                skill_names.append(str(skill))
        story.append(_paragraph(", ".join(name for name in skill_names if name), body_style))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=str(resume.get("name") or "Resume"),
        author="Simplify Resume",
    )
    doc.build(story)
    return output_path
