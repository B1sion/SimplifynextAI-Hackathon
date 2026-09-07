from database.database import get_connection
from typing import Any
from ._common import row_to_dict


def get_watch_settings(person_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO watch_settings (person_id, enabled) VALUES (?, 0)",
            (person_id,),
        )
        row = row_to_dict(
            connection.execute(
                "SELECT * FROM watch_settings WHERE person_id = ?", (person_id,)
            ).fetchone()
        )
    row["enabled"] = bool(row["enabled"])
    return row


def set_watch_enabled(person_id: int, enabled: bool) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            """INSERT INTO watch_settings (person_id, enabled) VALUES (?, ?)
            ON CONFLICT(person_id) DO UPDATE SET
                enabled = excluded.enabled,
                updated_at = CURRENT_TIMESTAMP""",
            (person_id, int(enabled)),
        )
    return get_watch_settings(person_id)
