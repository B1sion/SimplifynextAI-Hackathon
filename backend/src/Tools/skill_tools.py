from database.database import get_connection
from typing import Any
from ._common import row_to_dict, rows_to_dicts


def create_skill(name: str, category: str | None = None) -> int:
    with get_connection() as connection:
        connection.execute("INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)", (name, category))
        row = connection.execute("SELECT * FROM skills WHERE name = ?", (name,)).fetchone()
        return row["id"]


def get_skill(skill_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone())


def get_skill_by_name(name: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM skills WHERE name = ?", (name,)).fetchone())


def add_skill_to_resume(resume_id: int, skill_id: int, source: str = "explicit", confidence: float | None = None, evidence: str | None = None) -> list[dict[str, Any]]:
    if source not in {"explicit", "inferred"}:
        raise ValueError("source must be 'explicit' or 'inferred'")
    with get_connection() as connection:
        connection.execute(
            """INSERT INTO resume_skills (resume_id, skill_id, source, confidence, evidence)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(resume_id, skill_id) DO UPDATE SET source=excluded.source,
            confidence=excluded.confidence, evidence=excluded.evidence""",
            (resume_id, skill_id, source, confidence, evidence),
        )
    return get_resume_skills(resume_id)


def get_resume_skills(resume_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        return rows_to_dicts(connection.execute(
            """SELECT s.id, s.name, s.category, rs.source, rs.confidence, rs.evidence
            FROM resume_skills rs JOIN skills s ON s.id = rs.skill_id
            WHERE rs.resume_id = ? ORDER BY s.name""", (resume_id,)
        ))


def remove_skill_from_resume(resume_id: int, skill_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM resume_skills WHERE resume_id = ? AND skill_id = ?", (resume_id, skill_id))
        return cursor.rowcount > 0
