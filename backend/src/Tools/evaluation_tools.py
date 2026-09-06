from database.database import get_connection
from ._common import dumps, loads, row_to_dict, rows_to_dicts


def save_evaluation(optimization_run_id, resume_version_id, iteration, score, evaluation_json):
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO evaluations
            (optimization_run_id, resume_version_id, iteration, score, evaluation_json)
            VALUES (?, ?, ?, ?, ?)""",
            (optimization_run_id, resume_version_id, iteration, score, dumps(evaluation_json)),
        )
        evaluation_id = cursor.lastrowid
    return get_evaluation(evaluation_id)


def get_evaluation(evaluation_id):
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)).fetchone())
    if row:
        row["evaluation_json"] = loads(row["evaluation_json"])
    return row


def get_latest_evaluation(run_id):
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM evaluations WHERE optimization_run_id = ? ORDER BY iteration DESC, id DESC LIMIT 1", (run_id,)).fetchone())
    if row:
        row["evaluation_json"] = loads(row["evaluation_json"])
    return row


def get_evaluations_for_run(run_id):
    with get_connection() as connection:
        rows = rows_to_dicts(connection.execute("SELECT * FROM evaluations WHERE optimization_run_id = ? ORDER BY iteration, id", (run_id,)))
    for row in rows:
        row["evaluation_json"] = loads(row["evaluation_json"])
    return rows
