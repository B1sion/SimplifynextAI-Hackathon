from database.database import get_connection
from ._common import dumps, loads, row_to_dict, rows_to_dicts


def create_resume(person_id, resume_name, original_file_path=None, raw_text=None, resume_json=None):
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO resumes
            (person_id, resume_name, original_file_path, raw_text, resume_json)
            VALUES (?, ?, ?, ?, ?)""",
            (person_id, resume_name, original_file_path, raw_text, dumps(resume_json)),
        )
        return cursor.lastrowid


def get_resume(resume_id):
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone())
    if row:
        row["resume_json"] = loads(row["resume_json"])
    return row


def get_latest_resume():
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM resumes ORDER BY id DESC LIMIT 1").fetchone())
    if row:
        row["resume_json"] = loads(row["resume_json"])
    return row


def get_resumes_for_person(person_id):
    with get_connection() as connection:
        rows = rows_to_dicts(connection.execute("SELECT * FROM resumes WHERE person_id = ? ORDER BY id", (person_id,)))
    for row in rows:
        row["resume_json"] = loads(row["resume_json"])
    return rows


def update_resume(resume_id, **fields):
    allowed = {"resume_name", "original_file_path", "raw_text", "resume_json"}
    changes = [(name, dumps(value) if name == "resume_json" else value) for name, value in fields.items() if name in allowed]
    if changes:
        assignments = ", ".join(f"{name} = ?" for name, _ in changes)
        with get_connection() as connection:
            connection.execute(
                f"UPDATE resumes SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [v for _, v in changes] + [resume_id],
            )
    return get_resume(resume_id)


def get_full_resume(resume_id):
    resume = get_resume(resume_id)
    if resume is None:
        return None
    with get_connection() as connection:
        person = row_to_dict(connection.execute(
            "SELECT p.* FROM people p JOIN resumes r ON r.person_id = p.id WHERE r.id = ?", (resume_id,)
        ).fetchone())
        experiences = rows_to_dicts(connection.execute(
            "SELECT * FROM work_experiences WHERE resume_id = ? ORDER BY experience_order, id", (resume_id,)
        ))
        for experience in experiences:
            experience["bullets"] = [row["bullet_text"] for row in connection.execute(
                "SELECT bullet_text FROM experience_bullets WHERE experience_id = ? ORDER BY bullet_order, id",
                (experience["id"],),
            )]
        education = rows_to_dicts(connection.execute("SELECT * FROM education WHERE resume_id = ? ORDER BY education_order, id", (resume_id,)))
        projects = rows_to_dicts(connection.execute("SELECT * FROM projects WHERE resume_id = ? ORDER BY project_order, id", (resume_id,)))
        skills = rows_to_dicts(connection.execute(
            """SELECT s.name, s.category, rs.source, rs.confidence, rs.evidence
            FROM resume_skills rs JOIN skills s ON s.id = rs.skill_id WHERE rs.resume_id = ? ORDER BY s.name""", (resume_id,)
        ))
    return {
        "resume_id": resume_id,
        "person": person,
        "resume": {"name": resume["resume_name"], "raw_text": resume["raw_text"], "resume_json": resume["resume_json"]},
        "work_experience": experiences,
        "education": education,
        "projects": projects,
        "skills": skills,
    }
