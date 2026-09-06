from database.database import get_connection
from ._common import row_to_dict, rows_to_dicts


def add_education(resume_id, institution, degree=None, field_of_study=None, start_date=None, end_date=None, grade=None, description=None, education_order=0):
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO education
            (resume_id, institution, degree, field_of_study, start_date, end_date, grade, description, education_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (resume_id, institution, degree, field_of_study, start_date, end_date, grade, description, education_order),
        )
        return cursor.lastrowid


def get_resume_education(resume_id):
    with get_connection() as connection:
        return rows_to_dicts(connection.execute("SELECT * FROM education WHERE resume_id = ? ORDER BY education_order, id", (resume_id,)))


def update_education(education_id, **fields):
    allowed = {"institution", "degree", "field_of_study", "start_date", "end_date", "grade", "description", "education_order"}
    changes = [(n, v) for n, v in fields.items() if n in allowed]
    if changes:
        with get_connection() as connection:
            connection.execute(f"UPDATE education SET {', '.join(f'{n} = ?' for n, _ in changes)} WHERE id = ?", [v for _, v in changes] + [education_id])
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM education WHERE id = ?", (education_id,)).fetchone())


def delete_education(education_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM education WHERE id = ?", (education_id,))
        return cursor.rowcount > 0


def add_project(resume_id, project_name, description=None, project_url=None, start_date=None, end_date=None, project_order=0):
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO projects
            (resume_id, project_name, description, project_url, start_date, end_date, project_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (resume_id, project_name, description, project_url, start_date, end_date, project_order),
        )
        return cursor.lastrowid


def get_resume_projects(resume_id):
    with get_connection() as connection:
        return rows_to_dicts(connection.execute("SELECT * FROM projects WHERE resume_id = ? ORDER BY project_order, id", (resume_id,)))


def update_project(project_id, **fields):
    allowed = {"project_name", "description", "project_url", "start_date", "end_date", "project_order"}
    changes = [(n, v) for n, v in fields.items() if n in allowed]
    if changes:
        with get_connection() as connection:
            connection.execute(f"UPDATE projects SET {', '.join(f'{n} = ?' for n, _ in changes)} WHERE id = ?", [v for _, v in changes] + [project_id])
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())


def delete_project(project_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cursor.rowcount > 0
