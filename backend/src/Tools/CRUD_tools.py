import sqlite3
from database.database import get_connection


def add_job(
    job_title,
    company_name,
    job_description,
    category,
    salary_min=None,
    salary_max=None,
    salary_currency=None,
    salary_period=None,
    min_years_experience=None,
    max_years_experience=None,
    website=None,
    job_url=None,
    location=None,
    work_arrangement=None,
    employment_type=None,
    date_posted=None
) -> int:
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO jobs (
            job_title,
            company_name,
            job_description,
            category,
            salary_min,
            salary_max,
            salary_currency,
            salary_period,
            min_years_experience,
            max_years_experience,
            website,
            job_url,
            location,
            work_arrangement,
            employment_type,
            date_posted
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_title,
            company_name,
            job_description,
            category,
            salary_min,
            salary_max,
            salary_currency,
            salary_period,
            min_years_experience,
            max_years_experience,
            website,
            job_url,
            location,
            work_arrangement,
            employment_type,
            date_posted
        )
    )

    job_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return job_id

def get_job(job_id) -> dict:
    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    )

    job = cursor.fetchone()

    connection.close()

    if job is None:
        return None

    return dict(job)

