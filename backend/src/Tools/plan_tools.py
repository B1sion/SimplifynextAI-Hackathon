from database.database import get_connection
from typing import Any
from ._common import dumps, loads, row_to_dict


def save_rewrite_plan(optimization_run_id: int, evaluation_id: int, resume_version_id: int, iteration: int, plan_json: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO rewrite_plans
            (optimization_run_id, evaluation_id, resume_version_id, iteration, plan_json)
            VALUES (?, ?, ?, ?, ?)""",
            (optimization_run_id, evaluation_id, resume_version_id, iteration, dumps(plan_json)),
        )
        plan_id = cursor.lastrowid
    return get_rewrite_plan(plan_id)


def get_rewrite_plan(plan_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM rewrite_plans WHERE id = ?", (plan_id,)).fetchone())
    if row:
        row["plan_json"] = loads(row["plan_json"])
    return row


def get_latest_rewrite_plan(run_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM rewrite_plans WHERE optimization_run_id = ? ORDER BY iteration DESC, id DESC LIMIT 1", (run_id,)).fetchone())
    if row:
        row["plan_json"] = loads(row["plan_json"])
    return row
