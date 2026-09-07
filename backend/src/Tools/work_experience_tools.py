from database.database import get_connection
from ._common import row_to_dict, rows_to_dicts


def add_work_experience(resume_id, company_name, job_title, location=None, start_date=None, end_date=None, description=None, experience_order=0):
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO work_experiences
            (resume_id, company_name, job_title, location, start_date, end_date, description, experience_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (resume_id, company_name, job_title, location, start_date, end_date, description, experience_order),
        )
        return cursor.lastrowid


def get_work_experience(experience_id):
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM work_experiences WHERE id = ?", (experience_id,)).fetchone())


def get_resume_work_experiences(resume_id):
    with get_connection() as connection:
        return rows_to_dicts(connection.execute("SELECT * FROM work_experiences WHERE resume_id = ? ORDER BY experience_order, id", (resume_id,)))


def update_work_experience(experience_id, **fields):
    allowed = {"company_name", "job_title", "location", "start_date", "end_date", "description", "experience_order"}
    changes = [(name, value) for name, value in fields.items() if name in allowed]
    if changes:
        with get_connection() as connection:
            connection.execute(
                f"UPDATE work_experiences SET {', '.join(f'{n} = ?' for n, _ in changes)} WHERE id = ?",
                [v for _, v in changes] + [experience_id],
            )
    return get_work_experience(experience_id)


def delete_work_experience(experience_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM work_experiences WHERE id = ?", (experience_id,))
        return cursor.rowcount > 0


def add_experience_bullet(experience_id, bullet_text, bullet_order=0):
    with get_connection() as connection:
        cursor = connection.execute("INSERT INTO experience_bullets (experience_id, bullet_order, bullet_text) VALUES (?, ?, ?)", (experience_id, bullet_order, bullet_text))
        return cursor.lastrowid


def update_experience_bullet(bullet_id, bullet_text=None, bullet_order=None):
    changes = [("bullet_text", bullet_text), ("bullet_order", bullet_order)]
    changes = [(n, v) for n, v in changes if v is not None]
    if changes:
        with get_connection() as connection:
            connection.execute(f"UPDATE experience_bullets SET {', '.join(f'{n} = ?' for n, _ in changes)} WHERE id = ?", [v for _, v in changes] + [bullet_id])
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM experience_bullets WHERE id = ?", (bullet_id,)).fetchone())


def delete_experience_bullet(bullet_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM experience_bullets WHERE id = ?", (bullet_id,))
        return cursor.rowcount > 0


def get_experience_bullets(experience_id):
    with get_connection() as connection:
        return rows_to_dicts(connection.execute("SELECT * FROM experience_bullets WHERE experience_id = ? ORDER BY bullet_order, id", (experience_id,)))
