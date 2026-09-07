from database.database import get_connection
from typing import Any
from ._common import row_to_dict


def create_person(name: str, email: str | None = None, phone: str | None = None, location: str | None = None, linkedin_url: str | None = None, github_url: str | None = None, portfolio_url: str | None = None) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO people
            (name, email, phone, location, linkedin_url, github_url, portfolio_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, email, phone, location, linkedin_url, github_url, portfolio_url),
        )
        return cursor.lastrowid


def get_person(person_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone())


def update_person(person_id: int, **fields: Any) -> dict[str, Any] | None:
    allowed = {"name", "email", "phone", "location", "linkedin_url", "github_url", "portfolio_url"}
    changes = [(name, value) for name, value in fields.items() if name in allowed]
    if changes:
        assignments = ", ".join(f"{name} = ?" for name, _ in changes)
        with get_connection() as connection:
            connection.execute(
                f"UPDATE people SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [v for _, v in changes] + [person_id],
            )
    return get_person(person_id)
