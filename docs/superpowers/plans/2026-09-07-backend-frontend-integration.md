# Backend/Frontend Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the FastAPI backend in `backend/` actually usable by the Next.js frontend in `lib/api.ts` — fix the response shapes of existing endpoints, enable cross-origin requests, and add the missing endpoints the frontend contract requires (profile, discover summary/unlocks, compass stub, watch toggle/stub feed, applications tracker, session summary).

**Architecture:** Keep the existing `Tools/*.py` (raw SQL, dict in/out) + `main.py` (FastAPI routes) pattern. Add one new `src/services/job_ranking.py` module to centralize "evaluate every stored job against a resume" logic (reused by three endpoints), and one new `src/services/presenters.py` module to centralize response shaping (verdict/score mapping, fact grouping) so it isn't duplicated across endpoints. Add four new SQLite tables (`profile_answers`, `compass_reports`, `watch_settings`, `applications`) via the existing `initialize_database()` script, plus one `Tools/*.py` module per new table, matching existing conventions exactly.

**Tech Stack:** Python 3.14, FastAPI, SQLite (stdlib `sqlite3`), Pydantic (via existing `contracts.py`), `unittest` (existing test framework — no pytest, no TestClient/httpx; tests call route functions directly, matching `backend/tests/test_api.py`).

**Spec:** This plan file is self-contained; the design was worked out interactively (see conversation history). Key confirmed decisions, copied verbatim:
- Persist real SQLite tables for: profile answers, watch on/off toggle, applications. (User: "A" to real-table persistence.)
- `/jobs/{id}/compass` (COMPASS/Employment-Pass scoring): schema exists in SQLite for future work, but the endpoint returns a fixed stub — no real scoring logic. (User: "skip implementation but include in sqlite table design... just stub the /pass data".)
- `/watch` feed: real `enabled` toggle persisted; the event feed itself is a stub (no scheduler exists). (User: "C".)
- Recruiter contacts (`/act` "reach" tab) and interview prep questions (`/act` "prep" tab): **out of scope** — another contributor owns these. Do not touch `ReachTab`/`PrepTab` data needs.
- `GET /applications`: real table + endpoint, returns empty list until a "mark as applied" UI action exists later (also out of scope now). (User: confirmed Option B.)
- Skill unlocks (`GET /jobs/unlocks`): `jobs` count computed for real from stored job descriptions; `weeks` is a small hardcoded lookup table with a default fallback (clearly not real data). (User: "A".)
- No auth exists or is being added. All new/fixed endpoints accept an optional `resume_id` query param and default to "the most recently uploaded resume" when omitted — matching the existing convention in `GET /jobs/{id}/match`. (User: confirmed Option A.)
- CORS middleware must be added — verified live that `OPTIONS /jobs` currently returns `405` and `GET /jobs` returns no `access-control-allow-origin` header, which silently breaks every browser fetch from `http://localhost:3000`.
- Existing `GET /jobs`, `GET /resumes/{id}/facts`, `GET /jobs/{id}/match` do not match the frontend's TypeScript contract (`lib/types.ts`) and must be reshaped, not left alongside a second "raw" endpoint.
- DOCX/Word resume upload is **not** implemented in this plan (no DOCX-parsing dependency exists in `requirements.txt`, and adding one is a separate feature decision). This is a known limitation, listed at the end of this plan, not silently ignored.

## Global Constraints

- Follow existing `Tools/*.py` conventions exactly: plain functions, `with get_connection() as connection:`, `row_to_dict`/`rows_to_dicts`/`dumps`/`loads` from `src/Tools/_common.py`, no ORM.
- All new tables are added inside the single `executescript(...)` call in `backend/database/database.py::initialize_database()`, as `CREATE TABLE IF NOT EXISTS`, matching the existing block's formatting (4-space nested indent, blank line between tables).
- All new/changed endpoint tests call the Python route function directly (e.g. `list_jobs(...)`), never `TestClient`/HTTP — matching `backend/tests/test_api.py` and `backend/tests/test_tools.py`.
- Every new/changed endpoint keeps the existing 404-on-missing-resource behavior (`HTTPException(status_code=404, ...)`) already used throughout `main.py`.
- Every new/changed endpoint that depends on Bedrock (`evaluate_resume`) must not let one job's `BedrockClientError` fail the entire response — wrap per-job and degrade gracefully (this is a direct, justified fix tightly coupled to the reshaping work, not scope creep).
- Money/points/percentages returned to the frontend must use the exact field names in `lib/types.ts` (`score`, `verdict`, `verdictLabel`, `pct`, `jobs`, `weeks`, etc.) — copy them verbatim, do not invent alternate names.
- Run `python -m unittest discover -s backend/tests -v` (from repo root, with `backend` on `PYTHONPATH`, i.e. `cd backend && python -m unittest discover -s tests -v`) after every task and confirm all tests pass before committing.

---

## File Structure

New files:
- `backend/src/services/job_ranking.py` — `rank_jobs_for_resume(resume_id: int | None) -> list[dict]`: evaluates every stored job against a resume, tolerating per-job Bedrock failures.
- `backend/src/services/presenters.py` — pure shaping functions: `verdict_for_score`, `job_to_frontend`, `facts_to_groups`, `match_requirements_to_frontend`, `COMPASS_STUB`, `WORK_PASS_STUB`.
- `backend/src/Tools/profile_tools.py` — `save_profile_answers`, `get_profile_answers`.
- `backend/src/Tools/watch_tools.py` — `get_watch_settings`, `set_watch_enabled`.
- `backend/src/Tools/application_tools.py` — `create_application`, `get_applications_for_person`.
- `backend/tests/test_services.py` — unit tests for `job_ranking.py` and `presenters.py`.
- `backend/tests/test_new_tools.py` — unit tests for the three new `Tools/*.py` modules.

Modified files:
- `backend/database/database.py` — add four `CREATE TABLE IF NOT EXISTS` blocks to `initialize_database()`.
- `backend/src/app/main.py` — add CORS middleware; reshape `GET /jobs`, `GET /resumes/{resume_id}/facts`, `GET /jobs/{job_id}/match`; add `GET /jobs/summary`, `GET /jobs/unlocks`, `GET /jobs/{job_id}/compass`, `GET /profile/questions`, `PUT /profile`, `GET /watch`, `PUT /watch`, `GET /applications`, `GET /session`.
- `backend/tests/test_api.py` — update `test_jobs_and_resume_facts_endpoints` for the new `GET /jobs` and `GET /resumes/{id}/facts` shapes.

---

### Task 1: Add CORS middleware

**Files:**
- Modify: `backend/src/app/main.py:1-20`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `app` (the existing FastAPI instance) now has CORS middleware installed; later tasks are unaffected by this.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`, inside the existing `ApiTest` class (after `test_missing_resources_return_not_found`):

```python
    def test_cors_allows_frontend_origin(self):
        from starlette.testclient import TestClient
        from src.app.main import app

        with TestClient(app) as client:
            response = client.options(
                "/jobs",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api.ApiTest.test_cors_allows_frontend_origin -v`
Expected: FAIL — status code `405` instead of `200`, or missing `access-control-allow-origin` header (`KeyError`).

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add the import and middleware right after `app = FastAPI(title="Simplify Resume API")`:

```python
import os

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
```

```python
app = FastAPI(title="Simplify Resume API")

_ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
	if origin.strip()
]
app.add_middleware(
	CORSMiddleware,
	allow_origins=_ALLOWED_ORIGINS,
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)
```

(Note: the file uses tab indentation throughout — match that, not spaces.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api.ApiTest.test_cors_allows_frontend_origin -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS (no regressions).

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add CORS middleware for frontend origin"
```

---

### Task 2: Add new SQLite tables

**Files:**
- Modify: `backend/database/database.py` (inside `initialize_database()`, after the `rewrite_plans` table block, before the closing `"""`)
- Test: `backend/tests/test_new_tools.py` (new file — created fully in Task 3, but this task's step 2 uses a minimal inline check)

**Interfaces:**
- Consumes: nothing new.
- Produces: four new tables — `profile_answers`, `compass_reports`, `watch_settings`, `applications` — usable by `get_connection()` from any `Tools/*.py` module in later tasks.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_new_tools.py`:

```python
import tempfile
import unittest
from pathlib import Path

from database import database
from database.database import initialize_database, get_connection


class NewTablesTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.temp_dir.name) / "resume_builder.db"
        initialize_database()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_new_tables_exist(self):
        with get_connection() as connection:
            names = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        for table in ("profile_answers", "compass_reports", "watch_settings", "applications"):
            self.assertIn(table, names)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_new_tools -v`
Expected: FAIL — `AssertionError: 'profile_answers' not found in {...}`

- [ ] **Step 3: Write minimal implementation**

In `backend/database/database.py`, insert these four blocks into the `executescript(...)` string, immediately after the closing `);` of the `rewrite_plans` table and before the final `"""`:

```sql

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
```

`compass_reports` intentionally has no `Tools/*.py` reader/writer in this plan (the endpoint stub in Task 10 does not touch this table) — it exists purely so the schema is presentable, per the confirmed decision.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_new_tools -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS (no regressions — `initialize_database()` is additive only).

- [ ] **Step 6: Commit**

```bash
git add backend/database/database.py backend/tests/test_new_tools.py
git commit -m "feat(backend): add profile_answers, compass_reports, watch_settings, applications tables"
```

---

### Task 3: `profile_tools.py`, `watch_tools.py`, `application_tools.py`

**Files:**
- Create: `backend/src/Tools/profile_tools.py`
- Create: `backend/src/Tools/watch_tools.py`
- Create: `backend/src/Tools/application_tools.py`
- Modify: `backend/tests/test_new_tools.py`

**Interfaces:**
- Consumes: `get_connection` and `row_to_dict`/`rows_to_dicts` from `database.database` / `src.Tools._common` (existing).
- Produces:
  - `save_profile_answers(person_id: int, answers: dict[str, int]) -> list[dict]`
  - `get_profile_answers(person_id: int) -> list[dict]`
  - `get_watch_settings(person_id: int) -> dict` (always returns a row — creates one with `enabled=False` on first access)
  - `set_watch_enabled(person_id: int, enabled: bool) -> dict`
  - `create_application(person_id: int, job_id: int, status: str = "applied", verdict: str = "v") -> dict`
  - `get_applications_for_person(person_id: int) -> list[dict]`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_new_tools.py` (new imports at top, new test methods in `NewTablesTest`):

```python
from src.Tools.person_tools import create_person
from src.Tools.job_tools import add_job
from src.Tools.profile_tools import get_profile_answers, save_profile_answers
from src.Tools.watch_tools import get_watch_settings, set_watch_enabled
from src.Tools.application_tools import create_application, get_applications_for_person
```

```python
    def test_profile_answers_round_trip(self):
        person_id = create_person("Ada Lovelace")
        saved = save_profile_answers(person_id, {"work-status": 1, "qualification": 2})
        self.assertEqual(len(saved), 2)
        answers = get_profile_answers(person_id)
        by_question = {row["question_id"]: row["selected_index"] for row in answers}
        self.assertEqual(by_question, {"work-status": 1, "qualification": 2})

    def test_profile_answers_upsert_overwrites(self):
        person_id = create_person("Ada Lovelace")
        save_profile_answers(person_id, {"work-status": 1})
        save_profile_answers(person_id, {"work-status": 2})
        answers = get_profile_answers(person_id)
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0]["selected_index"], 2)

    def test_watch_settings_default_and_toggle(self):
        person_id = create_person("Ada Lovelace")
        settings = get_watch_settings(person_id)
        self.assertFalse(settings["enabled"])
        updated = set_watch_enabled(person_id, True)
        self.assertTrue(updated["enabled"])
        self.assertTrue(get_watch_settings(person_id)["enabled"])

    def test_applications_created_and_listed(self):
        person_id = create_person("Ada Lovelace")
        job_id = add_job("Engineer", "Build things", "Engineering", company_name="Analytical Engines")
        created = create_application(person_id, job_id, status="applied", verdict="v")
        self.assertEqual(created["status"], "applied")
        applications = get_applications_for_person(person_id)
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0]["job_id"], job_id)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_new_tools -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.Tools.profile_tools'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/src/Tools/profile_tools.py`:

```python
from database.database import get_connection
from typing import Any
from ._common import rows_to_dicts


def save_profile_answers(person_id: int, answers: dict[str, int]) -> list[dict[str, Any]]:
    with get_connection() as connection:
        for question_id, selected_index in answers.items():
            connection.execute(
                """INSERT INTO profile_answers (person_id, question_id, selected_index)
                VALUES (?, ?, ?)
                ON CONFLICT(person_id, question_id) DO UPDATE SET
                    selected_index = excluded.selected_index,
                    updated_at = CURRENT_TIMESTAMP""",
                (person_id, question_id, selected_index),
            )
    return get_profile_answers(person_id)


def get_profile_answers(person_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                "SELECT * FROM profile_answers WHERE person_id = ? ORDER BY question_id",
                (person_id,),
            )
        )
```

Create `backend/src/Tools/watch_tools.py`:

```python
from database.database import get_connection
from typing import Any
from ._common import row_to_dict


def get_watch_settings(person_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO watch_settings (person_id, enabled) VALUES (?, 0)",
            (person_id,),
        )
        row = row_to_dict(
            connection.execute(
                "SELECT * FROM watch_settings WHERE person_id = ?", (person_id,)
            ).fetchone()
        )
    row["enabled"] = bool(row["enabled"])
    return row


def set_watch_enabled(person_id: int, enabled: bool) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            """INSERT INTO watch_settings (person_id, enabled) VALUES (?, ?)
            ON CONFLICT(person_id) DO UPDATE SET
                enabled = excluded.enabled,
                updated_at = CURRENT_TIMESTAMP""",
            (person_id, int(enabled)),
        )
    return get_watch_settings(person_id)
```

Create `backend/src/Tools/application_tools.py`:

```python
from database.database import get_connection
from typing import Any
from ._common import row_to_dict, rows_to_dicts


def create_application(person_id: int, job_id: int, status: str = "applied", verdict: str = "v") -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO applications (person_id, job_id, status, verdict)
            VALUES (?, ?, ?, ?)""",
            (person_id, job_id, status, verdict),
        )
        application_id = cursor.lastrowid
    with get_connection() as connection:
        return row_to_dict(
            connection.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
        )


def get_applications_for_person(person_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                "SELECT * FROM applications WHERE person_id = ? ORDER BY sent_at DESC, id DESC",
                (person_id,),
            )
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_new_tools -v`
Expected: PASS (6 tests: `test_new_tables_exist`, `test_profile_answers_round_trip`, `test_profile_answers_upsert_overwrites`, `test_watch_settings_default_and_toggle`, `test_applications_created_and_listed`).

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/Tools/profile_tools.py backend/src/Tools/watch_tools.py backend/src/Tools/application_tools.py backend/tests/test_new_tools.py
git commit -m "feat(backend): add profile, watch, and application persistence tools"
```

---

### Task 4: `presenters.py` — response shaping helpers

**Files:**
- Create: `backend/src/services/presenters.py`
- Create: `backend/tests/test_services.py`

**Interfaces:**
- Consumes: nothing (pure functions operating on plain dicts).
- Produces:
  - `verdict_for_score(score: float) -> str` (`'v' | 'c' | 'b'`)
  - `DISCOVER_VERDICT_LABELS: dict[str, str]` (`{'v': 'Can apply', 'c': 'Might not qualify', 'b': 'Cannot apply'}`)
  - `job_to_frontend(job: dict, score: float | None) -> dict` (`Job` shape: `id, title, company, location, score, verdict, verdictLabel`)
  - `facts_to_groups(full_resume: dict) -> list[dict]` (`FactGroup[]` shape)
  - `find_skill_evidence(resume_skills: list[dict], skill_name: str) -> str`
  - `match_requirements_to_frontend(matched_skills: list[str], missing_skills: list[str], resume_skills: list[dict]) -> list[dict]` (`Requirement[]` shape)
  - `WORK_PASS_STUB: dict` (`{"points": 0, "needed": 40, "summary": "Work pass scoring is not available yet."}`)
  - `COMPASS_STUB_CRITERIA: list[dict]` and `compass_stub_report(job: dict) -> dict` (`CompassReport` shape)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_services.py`:

```python
import unittest

from src.services.presenters import (
    COMPASS_STUB_CRITERIA,
    WORK_PASS_STUB,
    compass_stub_report,
    facts_to_groups,
    find_skill_evidence,
    job_to_frontend,
    match_requirements_to_frontend,
    verdict_for_score,
)


class PresentersTest(unittest.TestCase):
    def test_verdict_for_score_thresholds(self):
        self.assertEqual(verdict_for_score(85), "v")
        self.assertEqual(verdict_for_score(70), "v")
        self.assertEqual(verdict_for_score(69.9), "c")
        self.assertEqual(verdict_for_score(50), "c")
        self.assertEqual(verdict_for_score(49.9), "b")
        self.assertEqual(verdict_for_score(0), "b")

    def test_job_to_frontend_shape(self):
        job = {"id": 3, "job_title": "Data Analyst", "company_name": "Grab", "location": "Singapore"}
        result = job_to_frontend(job, score=85)
        self.assertEqual(
            result,
            {
                "id": "3",
                "title": "Data Analyst",
                "company": "Grab",
                "location": "Singapore",
                "score": 9,
                "verdict": "v",
                "verdictLabel": "Can apply",
            },
        )

    def test_job_to_frontend_handles_missing_score(self):
        job = {"id": 1, "job_title": "Analyst", "company_name": None, "location": None}
        result = job_to_frontend(job, score=None)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["verdict"], "b")
        self.assertEqual(result["company"], "")
        self.assertEqual(result["location"], "")

    def test_facts_to_groups_covers_all_sections(self):
        full_resume = {
            "skills": [{"name": "Python", "category": "language", "evidence": "Built pipelines in Python"}],
            "work_experience": [
                {
                    "company_name": "Grab",
                    "job_title": "Analyst",
                    "bullets": ["Reduced churn by 12%"],
                }
            ],
            "education": [
                {"institution": "NUS", "degree": "BSc", "field_of_study": "Statistics", "description": None}
            ],
            "projects": [{"project_name": "Churn model", "description": "Predicted churn"}],
        }
        groups = facts_to_groups(full_resume)
        names = [g["group"] for g in groups]
        self.assertEqual(names, ["Skills", "Work Experience", "Education", "Projects"])
        self.assertEqual(groups[0]["items"][0]["value"], "Python")
        self.assertEqual(groups[0]["items"][0]["source"], "Built pipelines in Python")
        self.assertEqual(groups[1]["items"][0]["value"], "Reduced churn by 12%")
        self.assertEqual(groups[1]["items"][0]["location"], "Grab · Analyst")

    def test_facts_to_groups_skips_empty_sections(self):
        groups = facts_to_groups({"skills": [], "work_experience": [], "education": [], "projects": []})
        self.assertEqual(groups, [])

    def test_find_skill_evidence_matches_case_insensitively(self):
        resume_skills = [{"name": "python", "evidence": "5 years of Python"}]
        self.assertEqual(find_skill_evidence(resume_skills, "Python"), "5 years of Python")

    def test_find_skill_evidence_falls_back_when_not_found(self):
        self.assertEqual(find_skill_evidence([], "SQL"), "Found in resume")

    def test_match_requirements_to_frontend_shape(self):
        resume_skills = [{"name": "Python", "evidence": "5 years of Python"}]
        requirements = match_requirements_to_frontend(
            matched_skills=["Python"], missing_skills=["Docker"], resume_skills=resume_skills
        )
        self.assertEqual(
            requirements[0],
            {"met": True, "text": "Python", "evidence": "5 years of Python", "location": "Resume"},
        )
        self.assertEqual(
            requirements[1],
            {"met": False, "text": "Docker", "note": "Not found in the resume"},
        )

    def test_work_pass_stub_shape(self):
        self.assertEqual(set(WORK_PASS_STUB.keys()), {"points", "needed", "summary"})

    def test_compass_stub_report_shape(self):
        job = {"id": 5, "job_title": "Analyst", "company_name": "Grab", "location": "Singapore"}
        report = compass_stub_report(job)
        self.assertEqual(report["jobId"], "5")
        self.assertEqual(report["criteria"], COMPASS_STUB_CRITERIA)
        self.assertIn("disclaimer", report)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_services -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.services.presenters'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/src/services/presenters.py`:

```python
from typing import Any


DISCOVER_VERDICT_LABELS = {"v": "Can apply", "c": "Might not qualify", "b": "Cannot apply"}

WORK_PASS_STUB: dict[str, Any] = {
	"points": 0,
	"needed": 40,
	"summary": "Work pass scoring is not available yet.",
}

COMPASS_STUB_CRITERIA: list[dict[str, Any]] = [
	{"code": "C1", "name": "Salary", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C2", "name": "Qualifications", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C3", "name": "Diversity", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C4", "name": "Support for local employment", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C5", "name": "Skills bonus", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
	{"code": "C6", "name": "Strategic economic priorities bonus", "detail": "Not yet scored.", "points": 0, "verdict": "b"},
]


def verdict_for_score(score: float) -> str:
	if score >= 70:
		return "v"
	if score >= 50:
		return "c"
	return "b"


def job_to_frontend(job: dict[str, Any], score: float | None) -> dict[str, Any]:
	resolved_score = score if score is not None else 0
	verdict = verdict_for_score(resolved_score)
	return {
		"id": str(job["id"]),
		"title": job.get("job_title") or "",
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"score": round(resolved_score / 10),
		"verdict": verdict,
		"verdictLabel": DISCOVER_VERDICT_LABELS[verdict],
	}


def facts_to_groups(full_resume: dict[str, Any]) -> list[dict[str, Any]]:
	groups: list[dict[str, Any]] = []

	skills = full_resume.get("skills") or []
	if skills:
		groups.append(
			{
				"group": "Skills",
				"items": [
					{
						"value": skill.get("name") or "",
						"source": skill.get("evidence") or "No evidence captured",
						"location": f"Resume · {skill.get('category') or 'Skills'}",
					}
					for skill in skills
				],
			}
		)

	experiences = full_resume.get("work_experience") or []
	experience_items = [
		{
			"value": bullet,
			"source": bullet,
			"location": f"{experience.get('company_name') or ''} · {experience.get('job_title') or ''}",
		}
		for experience in experiences
		for bullet in (experience.get("bullets") or [])
	]
	if experience_items:
		groups.append({"group": "Work Experience", "items": experience_items})

	education = full_resume.get("education") or []
	if education:
		groups.append(
			{
				"group": "Education",
				"items": [
					{
						"value": f"{entry.get('degree') or ''} in {entry.get('field_of_study') or ''}".strip(" in ") or entry.get("institution") or "",
						"source": entry.get("description") or entry.get("institution") or "",
						"location": entry.get("institution") or "Education",
					}
					for entry in education
				],
			}
		)

	projects = full_resume.get("projects") or []
	if projects:
		groups.append(
			{
				"group": "Projects",
				"items": [
					{
						"value": project.get("project_name") or "",
						"source": project.get("description") or project.get("project_name") or "",
						"location": "Projects",
					}
					for project in projects
				],
			}
		)

	return groups


def find_skill_evidence(resume_skills: list[dict[str, Any]], skill_name: str) -> str:
	for skill in resume_skills:
		if str(skill.get("name", "")).casefold() == skill_name.casefold():
			return skill.get("evidence") or "Found in resume"
	return "Found in resume"


def match_requirements_to_frontend(
	matched_skills: list[str], missing_skills: list[str], resume_skills: list[dict[str, Any]]
) -> list[dict[str, Any]]:
	requirements: list[dict[str, Any]] = [
		{
			"met": True,
			"text": skill,
			"evidence": find_skill_evidence(resume_skills, skill),
			"location": "Resume",
		}
		for skill in matched_skills
	]
	requirements.extend(
		{"met": False, "text": skill, "note": "Not found in the resume"} for skill in missing_skills
	)
	return requirements


def compass_stub_report(job: dict[str, Any]) -> dict[str, Any]:
	return {
		"jobId": str(job["id"]),
		"jobTitle": job.get("job_title") or "",
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"needed": WORK_PASS_STUB["needed"],
		"criteria": COMPASS_STUB_CRITERIA,
		"closingTheGap": "Work pass scoring is not implemented yet.",
		"disclaimer": "This is a placeholder. COMPASS scoring has not been implemented.",
	}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_services -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/services/presenters.py backend/tests/test_services.py
git commit -m "feat(backend): add presenter functions for frontend response shaping"
```

---

### Task 5: `job_ranking.py` — centralized, resilient job scoring

**Files:**
- Create: `backend/src/services/job_ranking.py`
- Modify: `backend/tests/test_services.py`

**Interfaces:**
- Consumes: `get_all_jobs` (`src.Tools.job_tools`), `get_full_resume` (`src.Tools.resume_tools`), `parse_job` (`src.agents.resume_agents.job_parser`), `evaluate_resume` (`src.agents.resume_agents.evaluator`), `BedrockNovaClient`/`BedrockClientError` (`src.agents.resume_agents.bedrock_client`) — all existing.
- Produces: `rank_jobs_for_resume(resume: dict | None, model_client: Any) -> list[dict]`. Each returned dict is `{**job_row, "score": float, "evaluation": ATSReport | None}`. If evaluating a specific job raises `BedrockClientError`, that job gets `score=0.0, evaluation=None` instead of raising — evaluation of other jobs continues.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_services.py` (new imports at top):

```python
from unittest.mock import patch

from src.services.job_ranking import rank_jobs_for_resume


class JobRankingTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from database import database
        from database.database import initialize_database
        from src.Tools.job_tools import add_job
        from src.Tools.person_tools import create_person
        from src.Tools.resume_tools import create_resume, get_full_resume

        self.temp_dir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.temp_dir.name) / "resume_builder.db"
        initialize_database()
        self.person_id = create_person("Ada Lovelace")
        self.resume_id = create_resume(
            self.person_id, "Ada Resume", raw_text="Python developer", resume_json={"skills": ["Python"]}
        )
        self.job_with_python = add_job("Engineer A", "Needs Python", "Engineering", company_name="A")
        self.job_without_python = add_job("Engineer B", "Needs Rust", "Engineering", company_name="B")
        self.resume = get_full_resume(self.resume_id)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ranking_degrades_gracefully_on_bedrock_failure(self):
        from src.agents.resume_agents.bedrock_client import BedrockClientError

        with patch("src.services.job_ranking.evaluate_resume", side_effect=BedrockClientError("boom")):
            ranked = rank_jobs_for_resume(self.resume, model_client=object())

        self.assertEqual(len(ranked), 2)
        for entry in ranked:
            self.assertEqual(entry["score"], 0.0)
            self.assertIsNone(entry["evaluation"])

    def test_ranking_returns_scores_from_model_client(self):
        from src.agents.resume_agents.contracts import ATSReport

        def fake_evaluate(resume, job_ir, model_client):
            return ATSReport(ats_score=90.0) if job_ir.title == "Engineer A" else ATSReport(ats_score=40.0)

        with patch("src.services.job_ranking.evaluate_resume", side_effect=fake_evaluate):
            ranked = rank_jobs_for_resume(self.resume, model_client=object())

        scores = {entry["id"]: entry["score"] for entry in ranked}
        self.assertEqual(scores[self.job_with_python], 90.0)
        self.assertEqual(scores[self.job_without_python], 40.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_services -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.services.job_ranking'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/src/services/job_ranking.py`:

```python
from typing import Any

from src.Tools.job_tools import get_all_jobs
from src.agents.resume_agents.bedrock_client import BedrockClientError
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job


def rank_jobs_for_resume(resume: dict[str, Any] | None, model_client: Any) -> list[dict[str, Any]]:
	"""Evaluate every stored job against `resume`. One job's Bedrock failure
	degrades that job to score=0.0/evaluation=None instead of raising, so the
	caller always gets a full list back."""
	jobs = get_all_jobs()
	ranked: list[dict[str, Any]] = []
	for job in jobs:
		entry = {**job, "score": 0.0, "evaluation": None}
		if resume is not None:
			try:
				job_ir = parse_job(job)
				report = evaluate_resume(resume, job_ir, model_client)
				entry["score"] = report.ats_score
				entry["evaluation"] = report
			except BedrockClientError:
				pass
		ranked.append(entry)
	return ranked
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_services -v`
Expected: PASS (12 tests total)

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/services/job_ranking.py backend/tests/test_services.py
git commit -m "feat(backend): add resilient job ranking service"
```

---

### Task 6: Fix `GET /jobs` to return the frontend `Job[]` shape

**Files:**
- Modify: `backend/src/app/main.py:53-67` (the existing `list_jobs` function)
- Modify: `backend/tests/test_api.py` (`test_jobs_and_resume_facts_endpoints`)

**Interfaces:**
- Consumes: `rank_jobs_for_resume` (Task 5), `job_to_frontend` (Task 4), `get_latest_resume`/`get_full_resume` (existing `src.Tools.resume_tools`).
- Produces: `GET /jobs?mode=close|browse` returns a bare JSON array (`list[dict]`), each dict matching `lib/types.ts`'s `Job` interface exactly. `mode="close"` sorts by score descending; `mode="browse"` sorts alphabetically by title (matching the frontend's current fixture-mode fallback in `lib/api.ts::fetchJobs`).

- [ ] **Step 1: Write the failing test**

Replace the existing `test_jobs_and_resume_facts_endpoints` test in `backend/tests/test_api.py` with:

```python
    def test_list_jobs_returns_frontend_job_shape(self):
        jobs = list_jobs(mode="browse")
        self.assertIsInstance(jobs, list)
        self.assertEqual(
            set(jobs[0].keys()), {"id", "title", "company", "location", "score", "verdict", "verdictLabel"}
        )
        self.assertEqual(jobs[0]["id"], str(self.job_id))

    def test_list_jobs_close_mode_sorts_by_score_descending(self):
        second_job_id = add_job("Second Role", "Needs Python", "Engineering", company_name="Other Co")
        jobs = list_jobs(mode="close")
        ids = [job["id"] for job in jobs]
        self.assertEqual(set(ids), {str(self.job_id), str(second_job_id)})
        scores = [job["score"] for job in jobs]
        self.assertEqual(scores, sorted(scores, reverse=True))
```

Also remove the now-stale `facts = resume_facts(self.resume_id)` / `self.assertEqual(facts["person"]["name"], ...)` assertions from that old test — they move to Task 7's test. Keep the `test_optimization_context_and_versions_endpoints` and `test_missing_resources_return_not_found` tests unchanged.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `KeyError` or `AssertionError` because `list_jobs` still returns the old `{"jobs": ..., "ranked": ..., "mode": ...}` wrapper shape.

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, replace the existing `list_jobs` function:

```python
@app.get("/jobs")
def list_jobs(resume_id: int | None = Query(default=None), mode: str = Query(default="browse")) -> list[dict[str, Any]]:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	resume = get_full_resume(resume_record["id"]) if resume_record is not None else None
	ranked = rank_jobs_for_resume(resume, BedrockNovaClient())
	jobs = [job_to_frontend(entry, entry["score"] if resume is not None else None) for entry in ranked]
	if mode == "close" and resume is not None:
		jobs.sort(key=lambda job: job["score"], reverse=True)
	else:
		jobs.sort(key=lambda job: job["title"].casefold())
	return jobs
```

Add the needed imports at the top of `main.py`:

```python
from src.Tools.resume_tools import get_full_resume, get_latest_resume, get_resume
from src.services.job_ranking import rank_jobs_for_resume
from src.services.presenters import job_to_frontend
```

(Remove the old inline `from src.Tools.resume_tools import get_resume` that previously lived inside `match_job` — it becomes redundant since `get_resume` is now imported at module scope. Check for and remove that duplicate local import inside `match_job` in Task 8.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "fix(backend): reshape GET /jobs to match frontend Job[] contract"
```

---

### Task 7: Fix `GET /resumes/{resume_id}/facts` to return `FactGroup[]`

**Files:**
- Modify: `backend/src/app/main.py:71-76` (the existing `resume_facts` function)
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `facts_to_groups` (Task 4), existing `get_full_resume`.
- Produces: `GET /resumes/{resume_id}/facts` returns a bare JSON array matching `lib/types.ts`'s `FactGroup[]`.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py` (inside `ApiTest`, and extend `setUp` to add a skill so facts are non-empty):

```python
    def test_resume_facts_returns_fact_groups(self):
        from src.Tools.skill_tools import add_skill_to_resume, create_skill

        skill_id = create_skill("Python")
        add_skill_to_resume(self.resume_id, skill_id, source="explicit", evidence="Python developer")
        facts = resume_facts(self.resume_id)
        self.assertIsInstance(facts, list)
        skills_group = next(g for g in facts if g["group"] == "Skills")
        self.assertEqual(skills_group["items"][0]["value"], "Python")
        self.assertEqual(skills_group["items"][0]["source"], "Python developer")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `TypeError: list indices must be integers` (current return is a dict with `person`/`resume`/`work_experience` keys, not a list of groups).

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, replace `resume_facts`:

```python
@app.get("/resumes/{resume_id}/facts")
def resume_facts(resume_id: int) -> list[dict[str, Any]]:
	resume = get_full_resume(resume_id)
	if resume is None:
		raise HTTPException(status_code=404, detail="Resume not found")
	return facts_to_groups(resume)
```

Add to the imports:

```python
from src.services.presenters import facts_to_groups, job_to_frontend
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "fix(backend): reshape GET /resumes/:id/facts to match frontend FactGroup[] contract"
```

---

### Task 8: Fix `GET /jobs/{job_id}/match` — add `workPass` and `evidence`

**Files:**
- Modify: `backend/src/app/main.py:180-220` (the existing `match_job` function)
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `match_requirements_to_frontend`, `WORK_PASS_STUB` (Task 4).
- Produces: `GET /jobs/{job_id}/match` response now includes a `workPass: {points, needed, summary}` key, and each `met: true` requirement includes an `evidence` string (not just `location`).

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_match_job_includes_work_pass_and_evidence(self):
        from src.Tools.skill_tools import add_skill_to_resume, create_skill
        from unittest.mock import patch
        from src.agents.resume_agents.contracts import ATSReport

        skill_id = create_skill("Python")
        add_skill_to_resume(self.resume_id, skill_id, source="explicit", evidence="5 years of Python")
        fake_report = ATSReport(ats_score=80.0, matched_skills=["Python"], missing_skills=["Docker"])
        with patch("src.app.main.evaluate_resume", return_value=fake_report):
            response = match_job(self.job_id, resume_id=self.resume_id)
        self.assertIn("workPass", response)
        self.assertEqual(set(response["workPass"].keys()), {"points", "needed", "summary"})
        met_requirement = next(r for r in response["requirements"] if r["met"])
        self.assertEqual(met_requirement["evidence"], "5 years of Python")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `KeyError: 'workPass'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, inside `match_job`, replace the requirements-building block:

```python
	requirements = [
		{"met": True, "text": item, "location": "Resume"}
		for item in report.matched_skills
	]
	requirements.extend({"met": False, "text": item, "note": "Not found in the resume"} for item in report.missing_skills)
	return {
		"jobId": str(job_id),
		"jobTitle": job["job_title"],
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"verdict": "v" if report.ats_score >= 70 else "c" if report.ats_score >= 50 else "b",
		"verdictLabel": "Strong match" if report.ats_score >= 70 else "Review gaps",
		"score": report.ats_score,
		"agents": [{"name": "ATS evaluator", "ok": True, "detail": "Evaluation persisted locally"}],
		"requirements": requirements,
		"evaluationId": evaluation["id"],
		"evaluation": report.model_dump(),
	}
```

with:

```python
	requirements = match_requirements_to_frontend(
		matched_skills=report.matched_skills,
		missing_skills=report.missing_skills,
		resume_skills=resume.get("skills") or [],
	)
	return {
		"jobId": str(job_id),
		"jobTitle": job["job_title"],
		"company": job.get("company_name") or "",
		"location": job.get("location") or "",
		"verdict": "v" if report.ats_score >= 70 else "c" if report.ats_score >= 50 else "b",
		"verdictLabel": "Strong match" if report.ats_score >= 70 else "Review gaps",
		"score": report.ats_score,
		"agents": [{"name": "ATS evaluator", "ok": True, "detail": "Evaluation persisted locally"}],
		"requirements": requirements,
		"workPass": WORK_PASS_STUB,
		"evaluationId": evaluation["id"],
		"evaluation": report.model_dump(),
	}
```

Also remove the redundant local import inside `match_job` (`from src.Tools.resume_tools import get_resume`) since `get_resume` is now imported at module level (Task 6), and update the import list:

```python
from src.services.presenters import WORK_PASS_STUB, facts_to_groups, job_to_frontend, match_requirements_to_frontend
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "fix(backend): add workPass and evidence fields to GET /jobs/:id/match"
```

---

### Task 9: `GET /jobs/summary` — `DiscoverSummary`

**Files:**
- Modify: `backend/src/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `rank_jobs_for_resume` (Task 5), `verdict_for_score` (Task 4).
- Produces: `GET /jobs/summary` returns `{"totalRoles": int, "canApply": int, "mightNotQualify": int, "cannotApply": int}`, matching `lib/types.ts`'s `DiscoverSummary`.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_jobs_summary_counts_verdicts(self):
        from unittest.mock import patch
        from src.agents.resume_agents.contracts import ATSReport

        add_job("Second Role", "Needs Rust", "Engineering", company_name="Other Co")
        with patch("src.services.job_ranking.evaluate_resume", side_effect=[
            ATSReport(ats_score=80.0),
            ATSReport(ats_score=40.0),
        ]):
            summary = jobs_summary(resume_id=self.resume_id)
        self.assertEqual(summary["totalRoles"], 2)
        self.assertEqual(summary["canApply"], 1)
        self.assertEqual(summary["cannotApply"], 1)
        self.assertEqual(summary["mightNotQualify"], 0)
```

Add `jobs_summary` to the imports at the top of `test_api.py`:

```python
from src.app.main import jobs_summary, list_jobs, optimization_run, optimization_versions, resume_facts, match_job
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `ImportError: cannot import name 'jobs_summary'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add (placing it right after `list_jobs`):

```python
@app.get("/jobs/summary")
def jobs_summary(resume_id: int | None = Query(default=None)) -> dict[str, int]:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	resume = get_full_resume(resume_record["id"]) if resume_record is not None else None
	ranked = rank_jobs_for_resume(resume, BedrockNovaClient())
	counts = {"v": 0, "c": 0, "b": 0}
	for entry in ranked:
		counts[verdict_for_score(entry["score"] if resume is not None else 0)] += 1
	return {
		"totalRoles": len(ranked),
		"canApply": counts["v"],
		"mightNotQualify": counts["c"],
		"cannotApply": counts["b"],
	}
```

Add `verdict_for_score` to the presenters import line.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add GET /jobs/summary endpoint"
```

---

### Task 10: `GET /jobs/unlocks` — `SkillUnlock[]`

**Files:**
- Modify: `backend/src/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `rank_jobs_for_resume` (Task 5), `get_all_jobs` (existing).
- Produces: `GET /jobs/unlocks` returns a `list[dict]` matching `SkillUnlock` (`name, jobs, weeks, pct`). `jobs` is computed for real (count of stored job descriptions mentioning the skill); `weeks`/`pct` use a small hardcoded lookup table, clearly documented as an estimate.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_jobs_unlocks_counts_real_job_mentions(self):
        from unittest.mock import patch
        from src.agents.resume_agents.contracts import ATSReport

        add_job("SQL heavy role", "Must know SQL and Docker", "Engineering", company_name="Other Co")
        add_job("SQL only role", "Must know SQL", "Engineering", company_name="Third Co")
        with patch(
            "src.services.job_ranking.evaluate_resume",
            return_value=ATSReport(ats_score=40.0, missing_skills=["SQL", "Docker"]),
        ):
            unlocks = jobs_unlocks(resume_id=self.resume_id, limit=5)
        by_name = {u["name"]: u for u in unlocks}
        self.assertEqual(by_name["SQL"]["jobs"], 2)
        self.assertEqual(by_name["Docker"]["jobs"], 1)
        self.assertEqual(by_name["SQL"]["pct"], 100)
        self.assertIn("week", by_name["SQL"]["weeks"])
```

Add `jobs_unlocks` to the `test_api.py` import line.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `ImportError: cannot import name 'jobs_unlocks'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add:

```python
_LEARNING_TIME_WEEKS: dict[str, int] = {
	"python": 4, "sql": 3, "docker": 4, "kubernetes": 6, "aws": 6, "react": 5,
	"excel": 2, "power query": 3, "vba": 3, "tableau": 3, "looker": 2, "dbt": 6,
	"amplitude": 3, "figma": 2, "git": 2, "linux": 4,
}
_DEFAULT_LEARNING_WEEKS = 4


@app.get("/jobs/unlocks")
def jobs_unlocks(resume_id: int | None = Query(default=None), limit: int = Query(default=5, ge=1, le=20)) -> list[dict[str, Any]]:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	resume = get_full_resume(resume_record["id"]) if resume_record is not None else None
	ranked = rank_jobs_for_resume(resume, BedrockNovaClient())
	missing: set[str] = set()
	for entry in ranked:
		if entry["evaluation"] is not None:
			missing.update(entry["evaluation"].missing_skills)

	all_jobs = get_all_jobs()
	counts: list[tuple[str, int]] = []
	for skill in missing:
		count = sum(1 for job in all_jobs if skill.casefold() in (job.get("job_description") or "").casefold())
		counts.append((skill, count))
	counts.sort(key=lambda item: item[1], reverse=True)
	top = counts[:limit]
	max_count = max((count for _, count in top), default=0)

	return [
		{
			"name": skill,
			"jobs": count,
			"weeks": f"{_LEARNING_TIME_WEEKS.get(skill.casefold(), _DEFAULT_LEARNING_WEEKS)} weeks",
			"pct": round((count / max_count) * 100) if max_count else 0,
		}
		for skill, count in top
	]
```

Add `get_all_jobs` to the imports (it's already imported for `list_jobs`, confirm it's present once).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add GET /jobs/unlocks endpoint"
```

---

### Task 11: `GET /jobs/{job_id}/compass` — stub `CompassReport`

**Files:**
- Modify: `backend/src/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `compass_stub_report` (Task 4).
- Produces: `GET /jobs/{job_id}/compass` returns a `CompassReport`-shaped stub (404 if job not found).

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_jobs_compass_returns_stub(self):
        report = jobs_compass(self.job_id)
        self.assertEqual(report["jobId"], str(self.job_id))
        self.assertEqual(len(report["criteria"]), 6)

    def test_jobs_compass_missing_job_returns_404(self):
        with self.assertRaises(Exception):
            jobs_compass(999)
```

Add `jobs_compass` to the `test_api.py` import line.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `ImportError: cannot import name 'jobs_compass'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add:

```python
@app.get("/jobs/{job_id}/compass")
def jobs_compass(job_id: int) -> dict[str, Any]:
	job = get_job(job_id)
	if job is None:
		raise HTTPException(status_code=404, detail="Job not found")
	return compass_stub_report(job)
```

Add `compass_stub_report` to the presenters import line.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add stub GET /jobs/:id/compass endpoint"
```

---

### Task 12: `GET /profile/questions` and `PUT /profile`

**Files:**
- Modify: `backend/src/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `save_profile_answers` (Task 3), `get_latest_resume` (existing).
- Produces: `GET /profile/questions` returns the static `ProfileQuestion[]` catalog (mirrors `lib/data.ts::PROFILE_QUESTIONS`). `PUT /profile` accepts a JSON body `{"answers": {question_id: index}}` (optionally `?resume_id=`), persists via `profile_tools`, and returns `204 No Content` (matching `saveProfile(answers): Promise<void>` in `lib/api.ts`). Returns 404 if no resume/person exists yet (nothing to attach the answers to).

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_profile_questions_returns_static_catalog(self):
        questions = profile_questions()
        ids = [q["id"] for q in questions]
        self.assertIn("work-status", ids)
        self.assertIn("qualification", ids)

    def test_save_profile_persists_answers(self):
        from src.Tools.profile_tools import get_profile_answers

        save_profile(SaveProfileBody(answers={"work-status": 1}), resume_id=self.resume_id)
        person_id = get_resume(self.resume_id)["person_id"]
        answers = get_profile_answers(person_id)
        self.assertEqual(answers[0]["question_id"], "work-status")
        self.assertEqual(answers[0]["selected_index"], 1)

    def test_save_profile_without_any_resume_returns_404(self):
        from database import database
        from database.database import initialize_database
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as empty_dir:
            original_path = database.DATABASE_PATH
            database.DATABASE_PATH = Path(empty_dir) / "empty.db"
            initialize_database()
            try:
                with self.assertRaises(Exception):
                    save_profile(SaveProfileBody(answers={"work-status": 1}), resume_id=None)
            finally:
                database.DATABASE_PATH = original_path
```

Add `profile_questions, save_profile, SaveProfileBody` to the `test_api.py` import line.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `ImportError: cannot import name 'profile_questions'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add the Pydantic body model near the top (after existing imports), and the two routes:

```python
from pydantic import BaseModel


class SaveProfileBody(BaseModel):
	answers: dict[str, int]


_PROFILE_QUESTIONS: list[dict[str, Any]] = [
	{
		"id": "work-status",
		"question": "What is your work status in Singapore?",
		"options": ["Citizen or PR", "Needs an Employment Pass", "On a student pass"],
		"defaultPick": 1,
	},
	{
		"id": "qualification",
		"question": "Highest completed qualification",
		"options": ["Diploma", "Bachelor's", "Master's or above"],
		"defaultPick": 1,
	},
]


@app.get("/profile/questions")
def profile_questions() -> list[dict[str, Any]]:
	return _PROFILE_QUESTIONS


@app.put("/profile", status_code=204)
def save_profile(body: SaveProfileBody, resume_id: int | None = Query(default=None)) -> None:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	if resume_record is None:
		raise HTTPException(status_code=404, detail="No resume uploaded yet")
	save_profile_answers(resume_record["person_id"], body.answers)
```

Add `save_profile_answers` to the imports:

```python
from src.Tools.profile_tools import save_profile_answers
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add GET /profile/questions and PUT /profile endpoints"
```

---

### Task 13: `GET /watch` and `PUT /watch`

**Files:**
- Modify: `backend/src/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `get_watch_settings`, `set_watch_enabled` (Task 3).
- Produces: `GET /watch` returns a stub `WatchFeed` shape (`ranAt, postingsScanned, scope, enabled, events`) where `enabled` is the real persisted value and everything else is a fixed placeholder. `PUT /watch` accepts `{"enabled": bool}` and persists it, returning `204`.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_watch_feed_reflects_persisted_toggle(self):
        feed = watch_feed(resume_id=self.resume_id)
        self.assertFalse(feed["enabled"])
        self.assertEqual(feed["events"], [])

        set_watch(SetWatchBody(enabled=True), resume_id=self.resume_id)
        feed = watch_feed(resume_id=self.resume_id)
        self.assertTrue(feed["enabled"])
```

Add `watch_feed, set_watch, SetWatchBody` to the `test_api.py` import line.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `ImportError: cannot import name 'watch_feed'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add:

```python
class SetWatchBody(BaseModel):
	enabled: bool


@app.get("/watch")
def watch_feed(resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	enabled = False
	if resume_record is not None:
		enabled = get_watch_settings(resume_record["person_id"])["enabled"]
	return {
		"ranAt": "Not run yet",
		"postingsScanned": 0,
		"scope": "Overnight watch has not run yet.",
		"enabled": enabled,
		"events": [],
	}


@app.put("/watch", status_code=204)
def set_watch(body: SetWatchBody, resume_id: int | None = Query(default=None)) -> None:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	if resume_record is None:
		raise HTTPException(status_code=404, detail="No resume uploaded yet")
	set_watch_enabled(resume_record["person_id"], body.enabled)
```

Add to imports:

```python
from src.Tools.watch_tools import get_watch_settings, set_watch_enabled
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add GET /watch and PUT /watch endpoints"
```

---

### Task 14: `GET /applications`

**Files:**
- Modify: `backend/src/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `get_applications_for_person` (Task 3).
- Produces: `GET /applications` returns a `Tracker` shape (`{"metrics": [...], "applications": [...]}`). `applications` is real (empty until something calls `create_application`, which no endpoint does yet — documented limitation). `metrics` is computed from the (possibly empty) real list, not fabricated.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_applications_returns_real_empty_tracker(self):
        tracker = applications_tracker(resume_id=self.resume_id)
        self.assertEqual(tracker["applications"], [])
        self.assertEqual(tracker["metrics"][0], {"value": "0", "label": "applications sent"})

    def test_applications_reflects_created_rows(self):
        from src.Tools.application_tools import create_application

        person_id = get_resume(self.resume_id)["person_id"]
        create_application(person_id, self.job_id, status="Applied", verdict="v")
        tracker = applications_tracker(resume_id=self.resume_id)
        self.assertEqual(len(tracker["applications"]), 1)
        self.assertEqual(tracker["applications"][0]["job"], "Engineer")
        self.assertEqual(tracker["metrics"][0], {"value": "1", "label": "applications sent"})
```

Add `applications_tracker` to the `test_api.py` import line.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `ImportError: cannot import name 'applications_tracker'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add:

```python
@app.get("/applications")
def applications_tracker(resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	rows: list[dict[str, Any]] = []
	if resume_record is not None:
		rows = get_applications_for_person(resume_record["person_id"])

	applications = []
	for row in rows:
		job = get_job(row["job_id"])
		applications.append(
			{
				"id": str(row["id"]),
				"job": job["job_title"] if job else "",
				"company": (job.get("company_name") or "") if job else "",
				"sent": str(row["sent_at"]),
				"status": row["status"],
				"verdict": row["verdict"],
			}
		)

	return {
		"metrics": [{"value": str(len(applications)), "label": "applications sent"}],
		"applications": applications,
	}
```

Add to imports:

```python
from src.Tools.application_tools import get_applications_for_person
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add GET /applications endpoint"
```

---

### Task 15: `GET /session`

**Files:**
- Modify: `backend/src/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `get_full_resume`, `get_latest_resume`/`get_resume` (existing).
- Produces: `GET /session` returns a `SessionSummary` shape (`candidateName, factsConfirmed, claimsBlocked, lastWatchRun`). `candidateName` and `factsConfirmed` are computed from real data (person name; count of skills + experience bullets + education + project rows). `claimsBlocked` defaults to `0` and `lastWatchRun` to `"Not run yet"` — both honest fallbacks since no validation-report persistence or watch-run history exists (documented limitation, consistent with the compass/watch stub decisions).

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_api.py`:

```python
    def test_session_summary_counts_real_facts(self):
        from src.Tools.skill_tools import add_skill_to_resume, create_skill
        from src.Tools.work_experience_tools import add_experience_bullet, add_work_experience

        skill_id = create_skill("Python")
        add_skill_to_resume(self.resume_id, skill_id, source="explicit")
        experience_id = add_work_experience(self.resume_id, "Analytical Engines", "Engineer")
        add_experience_bullet(experience_id, "Built an engine")

        summary = session_summary(resume_id=self.resume_id)
        self.assertEqual(summary["candidateName"], "Ada Lovelace")
        self.assertEqual(summary["factsConfirmed"], 2)
        self.assertEqual(summary["claimsBlocked"], 0)
        self.assertEqual(summary["lastWatchRun"], "Not run yet")

    def test_session_summary_without_resume_returns_defaults(self):
        from database import database
        from database.database import initialize_database
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as empty_dir:
            original_path = database.DATABASE_PATH
            database.DATABASE_PATH = Path(empty_dir) / "empty.db"
            initialize_database()
            try:
                summary = session_summary(resume_id=None)
                self.assertEqual(summary["candidateName"], "")
                self.assertEqual(summary["factsConfirmed"], 0)
            finally:
                database.DATABASE_PATH = original_path
```

Add `session_summary` to the `test_api.py` import line.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: FAIL — `ImportError: cannot import name 'session_summary'`

- [ ] **Step 3: Write minimal implementation**

In `backend/src/app/main.py`, add:

```python
@app.get("/session")
def session_summary(resume_id: int | None = Query(default=None)) -> dict[str, Any]:
	resume_record = get_resume(resume_id) if resume_id is not None else get_latest_resume()
	if resume_record is None:
		return {"candidateName": "", "factsConfirmed": 0, "claimsBlocked": 0, "lastWatchRun": "Not run yet"}

	resume = get_full_resume(resume_record["id"])
	facts_confirmed = (
		len(resume.get("skills") or [])
		+ sum(len(experience.get("bullets") or []) for experience in (resume.get("work_experience") or []))
		+ len(resume.get("education") or [])
		+ len(resume.get("projects") or [])
	)
	return {
		"candidateName": (resume.get("person") or {}).get("name") or "",
		"factsConfirmed": facts_confirmed,
		"claimsBlocked": 0,
		"lastWatchRun": "Not run yet",
	}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m unittest tests.test_api -v`
Expected: PASS

- [ ] **Step 5: Run the full existing suite**

Run: `cd backend && python -m unittest discover -s tests -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): add GET /session endpoint"
```

---

### Task 16: Manual end-to-end verification against the running frontend

**Files:** none (verification only).

- [ ] **Step 1: Start the backend**

Run: `cd backend && uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload --env-file ../.env`

- [ ] **Step 2: Start the frontend**

Run (repo root): `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev`

- [ ] **Step 3: Walk every route with a real uploaded resume**

Upload a PDF at `/`, then visit `/facts`, `/profile`, `/discover`, `/match?job=<id>`, `/pass?job=<id>`, `/watch`, `/track`. Confirm each page renders without a thrown error (open browser dev tools console — zero uncaught exceptions) and confirm `Network` tab shows `200`/`204` responses with no CORS errors.

- [ ] **Step 4: Confirm `/act` and its "learn"/"tailor" tabs still work on fixture data**

`/act`'s `ActionCenter` (recruiters/interview-prep/diffs) is intentionally **not** wired to the backend in this plan (out of scope per the confirmed decisions) — `lib/api.ts::fetchActionCenter` still returns fixture data. Confirm the page still renders (it will, since `lib/api.ts` is untouched by this plan).

- [ ] **Step 5: Record results**

No commit for this task — it's a manual smoke test. If any step fails, open a follow-up task before considering this plan complete.

---

## Known Limitations (explicitly out of scope for this plan)

- **DOCX/Word resume upload:** `POST /resumes` still only accepts PDF. No DOCX-parsing dependency exists in `requirements.txt`; adding one (e.g. `python-docx`) is a separate feature decision not covered here.
- **`/act` "reach" (recruiter contacts) and "prep" (interview questions) tabs:** owned by another contributor; this plan does not touch their backend needs.
- **COMPASS/Employment Pass scoring:** `compass_reports` table exists in the schema; `GET /jobs/{id}/compass` and the `workPass` field in `GET /jobs/{id}/match` are fixed stubs, not real scoring.
- **Watch/overnight scanning:** the `enabled` toggle is real and persisted; there is no scheduler, so `GET /watch`'s event feed is always empty.
- **`claimsBlocked` in `GET /session`:** always `0` — no table persists `ValidationReport` data from the optimization orchestrator today, so there is nothing real to count.
- **`GET /applications`:** always empty until a future "mark as applied" UI action exists (out of scope here) — the endpoint and table are real, just unpopulated.
