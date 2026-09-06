import unittest
from unittest.mock import patch

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
from src.services.job_ranking import rank_jobs_for_resume


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


if __name__ == "__main__":
    unittest.main()
