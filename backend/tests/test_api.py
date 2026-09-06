import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from fastapi import HTTPException

from database import database
from database.database import initialize_database
from src.agents.resume_agents.contracts import ATSReport
from src.Tools.job_tools import add_job
from src.Tools.optimization_tools import create_optimization_run, create_resume_version
from src.Tools.person_tools import create_person
from src.Tools.resume_tools import create_resume, get_resume
from src.app.main import (
    SaveProfileBody,
    jobs_compass,
    jobs_summary,
    jobs_unlocks,
    list_jobs,
    match_job,
    optimization_run,
    optimization_versions,
    profile_questions,
    resume_facts,
    save_profile,
    SetWatchBody,
    set_watch,
    watch_feed,
)


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.temp_dir.name) / "resume_builder.db"
        initialize_database()
        person_id = create_person("Ada Lovelace", email="ada@example.com")
        self.resume_id = create_resume(
            person_id,
            "Ada Resume",
            raw_text="Python developer",
            resume_json={"name": "Ada Lovelace", "raw_text": "Python developer", "skills": ["Python"]},
        )
        self.job_id = add_job("Engineer", "Build Python systems", "Engineering", company_name="Analytical Engines")
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_jobs_returns_frontend_job_shape(self):
        jobs = list_jobs(mode="browse")
        self.assertIsInstance(jobs, list)
        self.assertEqual(
            set(jobs[0].keys()), {"id", "title", "company", "location", "score", "verdict", "verdictLabel"}
        )
        self.assertEqual(jobs[0]["id"], str(self.job_id))

    def test_list_jobs_close_mode_sorts_by_score_descending(self):
        second_job_id = add_job("Second Role", "Needs Python", "Engineering", company_name="Other Co")
        def fake_evaluate(resume, job_ir, model_client):
            scores = {"Engineer": 90.0, "Second Role": 40.0}
            return ATSReport(ats_score=scores[job_ir.title])

        with patch("src.services.job_ranking.evaluate_resume", side_effect=fake_evaluate):
            jobs = list_jobs(mode="close")

        ids = [job["id"] for job in jobs]
        self.assertEqual(set(ids), {str(self.job_id), str(second_job_id)})
        scores = [job["score"] for job in jobs]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_list_jobs_with_unknown_resume_id_returns_404(self):
        with self.assertRaises(HTTPException) as context:
            list_jobs(resume_id=999)
        self.assertEqual(context.exception.status_code, 404)

    def test_jobs_summary_counts_verdicts(self):
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

    def test_jobs_summary_with_unknown_resume_id_returns_404(self):
        with self.assertRaises(HTTPException) as context:
            jobs_summary(resume_id=999)
        self.assertEqual(context.exception.status_code, 404)

    def test_jobs_unlocks_counts_real_job_mentions(self):
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

    def test_jobs_unlocks_with_unknown_resume_id_returns_404(self):
        with self.assertRaises(HTTPException) as context:
            jobs_unlocks(resume_id=999)
        self.assertEqual(context.exception.status_code, 404)

    def test_resume_facts_returns_fact_groups(self):
        from src.Tools.skill_tools import add_skill_to_resume, create_skill

        skill_id = create_skill("Python")
        add_skill_to_resume(self.resume_id, skill_id, source="explicit", evidence="Python developer")
        facts = resume_facts(self.resume_id)
        self.assertIsInstance(facts, list)
        skills_group = next(g for g in facts if g["group"] == "Skills")
        self.assertEqual(skills_group["items"][0]["value"], "Python")
        self.assertEqual(skills_group["items"][0]["source"], "Python developer")

    def test_optimization_context_and_versions_endpoints(self):
        run = create_optimization_run(self.resume_id, self.job_id)
        create_resume_version(run["id"], {"name": "Ada Lovelace"}, version_number=0)
        response = optimization_versions(run["id"])

        self.assertEqual(len(response["versions"]), 1)
        self.assertEqual(response["comparisons"], [])
        self.assertEqual(optimization_run(run["id"])["run"]["id"], run["id"])

    def test_missing_resources_return_not_found(self):
        with self.assertRaises(Exception):
            resume_facts(999)
        with self.assertRaises(Exception):
            optimization_run(999)

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

    def test_match_job_includes_work_pass_and_evidence(self):
        from src.Tools.skill_tools import add_skill_to_resume, create_skill
        from src.app.main import match_job
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

    def test_jobs_compass_returns_stub(self):
        report = jobs_compass(self.job_id)
        self.assertEqual(report["jobId"], str(self.job_id))
        self.assertEqual(len(report["criteria"]), 6)

    def test_jobs_compass_missing_job_returns_404(self):
        with self.assertRaises(Exception):
            jobs_compass(999)

    def test_profile_questions_returns_static_catalog(self):
        questions = profile_questions()
        ids = [question["id"] for question in questions]
        self.assertIn("work-status", ids)
        self.assertIn("qualification", ids)
        self.assertIn("experience", ids)

    def test_save_profile_persists_answers(self):
        from src.Tools.profile_tools import get_profile_answers

        save_profile(SaveProfileBody(answers={"work-status": 1}), resume_id=self.resume_id)
        person_id = get_resume(self.resume_id)["person_id"]
        answers = get_profile_answers(person_id)
        self.assertEqual(answers[0]["question_id"], "work-status")
        self.assertEqual(answers[0]["selected_index"], 1)

    def test_save_profile_without_any_resume_returns_404(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            original_path = database.DATABASE_PATH
            database.DATABASE_PATH = Path(empty_dir) / "empty.db"
            initialize_database()
            try:
                with self.assertRaises(HTTPException) as context:
                    save_profile(SaveProfileBody(answers={"work-status": 1}), resume_id=None)
                self.assertEqual(context.exception.status_code, 404)
            finally:
                database.DATABASE_PATH = original_path

    def test_watch_feed_reflects_persisted_toggle(self):
        feed = watch_feed(resume_id=self.resume_id)
        self.assertFalse(feed["enabled"])
        self.assertEqual(feed["events"], [])

        set_watch(SetWatchBody(enabled=True), resume_id=self.resume_id)
        feed = watch_feed(resume_id=self.resume_id)
        self.assertTrue(feed["enabled"])

    def test_watch_feed_with_unknown_resume_id_returns_404(self):
        with self.assertRaises(HTTPException) as context:
            watch_feed(resume_id=999)
        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
