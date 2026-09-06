import sqlite3
from pathlib import Path
from typing import Any

DATABASE_PATH = Path(__file__).parent / "resume_builder.db"


class ManagedConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False


def get_connection() -> sqlite3.Connection:
    """Open a foreign-key-enforcing connection with automatic commit/rollback."""
    connection = sqlite3.connect(DATABASE_PATH, factory=ManagedConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Create the local schema; all application tables are intentionally SQLite-only."""
    connection = get_connection()

    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                location TEXT,
                linkedin_url TEXT,
                github_url TEXT,
                portfolio_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company_name TEXT,
                category TEXT NOT NULL CHECK (length(trim(category)) > 0),
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
            );

            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
                resume_name TEXT NOT NULL,
                original_file_path TEXT,
                raw_text TEXT,
                resume_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS work_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                company_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                location TEXT,
                start_date TEXT,
                end_date TEXT,
                description TEXT,
                experience_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS experience_bullets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experience_id INTEGER NOT NULL REFERENCES work_experiences(id) ON DELETE CASCADE,
                bullet_order INTEGER DEFAULT 0,
                bullet_text TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                institution TEXT NOT NULL,
                degree TEXT,
                field_of_study TEXT,
                start_date TEXT,
                end_date TEXT,
                grade TEXT,
                description TEXT,
                education_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                project_name TEXT NOT NULL,
                description TEXT,
                project_url TEXT,
                start_date TEXT,
                end_date TEXT,
                project_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT
            );

            CREATE TABLE IF NOT EXISTS resume_skills (
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
                source TEXT NOT NULL CHECK (source IN ('explicit', 'inferred')),
                confidence REAL,
                evidence TEXT,
                PRIMARY KEY (resume_id, skill_id)
            );

            CREATE TABLE IF NOT EXISTS optimization_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'created',
                current_iteration INTEGER NOT NULL DEFAULT 0,
                max_iterations INTEGER NOT NULL DEFAULT 3,
                initial_score REAL,
                current_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS resume_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_run_id INTEGER NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
                parent_version_id INTEGER REFERENCES resume_versions(id),
                version_number INTEGER NOT NULL,
                resume_json TEXT NOT NULL,
                rendered_file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (optimization_run_id, version_number)
            );

            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_run_id INTEGER NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
                resume_version_id INTEGER NOT NULL REFERENCES resume_versions(id) ON DELETE CASCADE,
                iteration INTEGER NOT NULL,
                score REAL NOT NULL,
                evaluation_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rewrite_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_run_id INTEGER NOT NULL REFERENCES optimization_runs(id) ON DELETE CASCADE,
                evaluation_id INTEGER NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
                resume_version_id INTEGER NOT NULL REFERENCES resume_versions(id) ON DELETE CASCADE,
                iteration INTEGER NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS profile_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
                question_id TEXT NOT NULL,
                selected_index INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (person_id, question_id)
            );

            CREATE TABLE IF NOT EXISTS compass_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                needed INTEGER NOT NULL,
                criteria_json TEXT NOT NULL,
                closing_the_gap TEXT,
                disclaimer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (person_id, job_id)
            );

            CREATE TABLE IF NOT EXISTS watch_settings (
                person_id INTEGER PRIMARY KEY REFERENCES people(id) ON DELETE CASCADE,
                enabled INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'applied',
                verdict TEXT NOT NULL DEFAULT 'v' CHECK (verdict IN ('v', 'c', 'b')),
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()