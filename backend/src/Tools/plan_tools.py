from database.database import get_connection
from ._common import dumps, loads, row_to_dict


def save_rewrite_plan(optimization_run_id, evaluation_id, resume_version_id, iteration, plan_json):
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO rewrite_plans
            (optimization_run_id, evaluation_id, resume_version_id, iteration, plan_json)
            VALUES (?, ?, ?, ?, ?)""",
            (optimization_run_id, evaluation_id, resume_version_id, iteration, dumps(plan_json)),
        )
        plan_id = cursor.lastrowid
    return get_rewrite_plan(plan_id)


def get_rewrite_plan(plan_id):
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM rewrite_plans WHERE id = ?", (plan_id,)).fetchone())
    if row:
        row["plan_json"] = loads(row["plan_json"])
    return row


def get_latest_rewrite_plan(run_id):
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM rewrite_plans WHERE optimization_run_id = ? ORDER BY iteration DESC, id DESC LIMIT 1", (run_id,)).fetchone())
    if row:
        row["plan_json"] = loads(row["plan_json"])
    return row
