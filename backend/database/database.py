import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "resume_builder.db"


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_title TEXT NOT NULL,
            category TEXT NOT NULL,
            company_name TEXT,

            salary_min INTEGER,
            salary_max INTEGER,
            salary_currency TEXT,
            salary_period TEXT,

            min_years_experience INTEGER,
            max_years_experience INTEGER,

            job_description TEXT NOT NULL,

            website TEXT,
            job_url TEXT,

            location TEXT,
            work_arrangement TEXT,
            employment_type TEXT,

            date_posted TEXT,
            date_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            status TEXT DEFAULT 'unknown'
        )
        """
    )

    connection.commit()
    connection.close()