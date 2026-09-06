import tempfile
import unittest
from pathlib import Path

from database import database
from database.database import initialize_database
from src.Tools.job_tools import add_job
from src.Tools.optimization_tools import create_optimization_run, create_resume_version
from src.Tools.person_tools import create_person
from src.Tools.resume_tools import create_resume
from src.app.main import list_jobs, optimization_run, optimization_versions, resume_facts


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

    def test_jobs_and_resume_facts_endpoints(self):
        jobs = list_jobs(resume_id=None, mode="browse")
        facts = resume_facts(self.resume_id)

        self.assertFalse(jobs["ranked"])
        self.assertEqual(jobs["jobs"][0]["id"], self.job_id)
        self.assertEqual(facts["person"]["name"], "Ada Lovelace")
        self.assertEqual(facts["resume"]["resume_json"]["skills"], ["Python"])

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


if __name__ == "__main__":
    unittest.main()
