from database.database import get_connection
from ._common import row_to_dict, rows_to_dicts


def _validate_category(category):
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category is required and must be a non-empty string")


def add_job(job_title, job_description, category, company_name=None, **fields):
    _validate_category(category)
    columns = ["job_title", "job_description", "category", "company_name"]
    values = [job_title, job_description, category, company_name]
    allowed = {
        "salary_min", "salary_max", "salary_currency", "salary_period",
        "min_years_experience", "max_years_experience", "website", "job_url",
        "location", "work_arrangement", "employment_type", "date_posted", "status",
    }
    for name, value in fields.items():
        if name in allowed:
            columns.append(name)
            values.append(value)
    placeholders = ", ".join("?" for _ in values)
    with get_connection() as connection:
        cursor = connection.execute(
            f"INSERT INTO jobs ({', '.join(columns)}) VALUES ({placeholders})", values
        )
        return cursor.lastrowid


def get_job(job_id):
    with get_connection() as connection:
        return row_to_dict(connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())


def get_all_jobs():
    with get_connection() as connection:
        return rows_to_dicts(connection.execute("SELECT * FROM jobs ORDER BY date_collected DESC, id DESC"))


def update_job(job_id, **fields):
    allowed = {
        "job_title", "company_name", "category", "salary_min", "salary_max", "salary_currency",
        "salary_period", "min_years_experience", "max_years_experience", "job_description",
        "website", "job_url", "location", "work_arrangement", "employment_type",
        "date_posted", "status",
    }
    changes = []
    for name, value in fields.items():
        if name in allowed:
            if name == "category":
                _validate_category(value)
            changes.append((name, value))
    if not changes:
        return get_job(job_id)
    assignments = ", ".join(f"{name} = ?" for name, _ in changes)
    with get_connection() as connection:
        connection.execute(f"UPDATE jobs SET {assignments} WHERE id = ?", [v for _, v in changes] + [job_id])
    return get_job(job_id)


def delete_job(job_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        return cursor.rowcount > 0
