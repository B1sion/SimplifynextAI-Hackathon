from database.database import get_connection
from typing import Any
from ._common import rows_to_dicts


def save_profile_answers(person_id: int, answers: dict[str, int]) -> list[dict[str, Any]]:
    with get_connection() as connection:
        for question_id, selected_index in answers.items():
            connection.execute(
                """INSERT INTO profile_answers (person_id, question_id, selected_index)
                VALUES (?, ?, ?)
                ON CONFLICT(person_id, question_id) DO UPDATE SET
                    selected_index = excluded.selected_index,
                    updated_at = CURRENT_TIMESTAMP""",
                (person_id, question_id, selected_index),
            )
    return get_profile_answers(person_id)


def get_profile_answers(person_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                "SELECT * FROM profile_answers WHERE person_id = ? ORDER BY question_id",
                (person_id,),
            )
        )
