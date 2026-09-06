from database.database import get_connection
from ._common import dumps, loads, row_to_dict, rows_to_dicts


def create_optimization_run(resume_id, job_id, max_iterations=3):
    with get_connection() as connection:
        resume = connection.execute("SELECT person_id FROM resumes WHERE id = ?", (resume_id,)).fetchone()
        if resume is None:
            return None
        cursor = connection.execute(
            "INSERT INTO optimization_runs (person_id, resume_id, job_id, max_iterations) VALUES (?, ?, ?, ?)",
            (resume["person_id"], resume_id, job_id, max_iterations),
        )
        run_id = cursor.lastrowid
    return get_optimization_run(run_id)


def get_optimization_run(run_id):
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM optimization_runs WHERE id = ?", (run_id,)).fetchone())


def update_optimization_status(run_id, status):
    with get_connection() as connection:
        connection.execute("UPDATE optimization_runs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, run_id))
    return get_optimization_run(run_id)


def increment_iteration(run_id):
    with get_connection() as connection:
        connection.execute("UPDATE optimization_runs SET current_iteration = current_iteration + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (run_id,))
    return get_optimization_run(run_id)


def complete_optimization_run(run_id, current_score=None):
    with get_connection() as connection:
        connection.execute("UPDATE optimization_runs SET status = 'completed', current_score = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (current_score, run_id))
    return get_optimization_run(run_id)


def create_resume_version(optimization_run_id, resume_json, rendered_file_path=None, parent_version_id=None, version_number=None):
    with get_connection() as connection:
        if version_number is None:
            row = connection.execute("SELECT COALESCE(MAX(version_number), -1) + 1 AS next_version FROM resume_versions WHERE optimization_run_id = ?", (optimization_run_id,)).fetchone()
            version_number = row["next_version"]
        cursor = connection.execute(
            """INSERT INTO resume_versions
            (optimization_run_id, parent_version_id, version_number, resume_json, rendered_file_path)
            VALUES (?, ?, ?, ?, ?)""",
            (optimization_run_id, parent_version_id, version_number, dumps(resume_json), rendered_file_path),
        )
        version_id = cursor.lastrowid
    return get_resume_version(version_id)


def get_resume_version(version_id):
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM resume_versions WHERE id = ?", (version_id,)).fetchone())
    if row:
        row["resume_json"] = loads(row["resume_json"])
    return row


def get_latest_resume_version(run_id):
    with get_connection() as connection:
        row = row_to_dict(connection.execute("SELECT * FROM resume_versions WHERE optimization_run_id = ? ORDER BY version_number DESC LIMIT 1", (run_id,)).fetchone())
    if row:
        row["resume_json"] = loads(row["resume_json"])
    return row


def get_resume_versions(run_id):
    with get_connection() as connection:
        rows = rows_to_dicts(connection.execute("SELECT * FROM resume_versions WHERE optimization_run_id = ? ORDER BY version_number", (run_id,)))
    for row in rows:
        row["resume_json"] = loads(row["resume_json"])
    return rows


def get_optimization_context(run_id):
    run = get_optimization_run(run_id)
    if run is None:
        return None
    return {"run": run, "resume": get_latest_resume_version(run_id), "evaluations": get_evaluations_for_run(run_id), "latest_plan": get_latest_rewrite_plan(run_id)}

from .evaluation_tools import get_evaluations_for_run
from .plan_tools import get_latest_rewrite_plan
