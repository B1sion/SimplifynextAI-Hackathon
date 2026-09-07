from database.database import get_connection
from typing import Any
from ._common import row_to_dict, rows_to_dicts


def create_application(person_id: int, job_id: int, status: str = "applied", verdict: str = "v") -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO applications (person_id, job_id, status, verdict)
            VALUES (?, ?, ?, ?)""",
            (person_id, job_id, status, verdict),
        )
        application_id = cursor.lastrowid
    with get_connection() as connection:
        return row_to_dict(
            connection.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
        )


def get_applications_for_person(person_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                "SELECT * FROM applications WHERE person_id = ? ORDER BY sent_at DESC, id DESC",
                (person_id,),
            )
        )
