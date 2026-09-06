import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from database import database
from database.database import initialize_database
from src.Tools.job_tools import add_job
from src.Tools.person_tools import create_person
from src.Tools.resume_tools import create_resume
from src.agents.resume_agents.contracts import InterviewPrep
from src.agents.resume_agents.interview_agent import generate_interview_questions
from src.agents.resume_agents.interview_validator import validate_interview
from src.agents.resume_agents.job_parser import parse_job
from src.app.main import interview_questions

from fastapi import HTTPException


RESUME_JSON = {
    "name": "Ada Lovelace",
    "raw_text": "Python developer with data analysis experience.",
    "skills": ["Python", "SQL"],
    "work_experience": [{"company_name": "Analytical Engines", "job_title": "Engineer", "description": "Built data systems."}],
}
RESUME_JSON_2 = {**RESUME_JSON, "name": "Grace Hopper"}

PREP = {
    "questions": [
        {"question": "Tell me about your Python experience.", "answer": "I built data systems at Analytical Engines using Python.", "use": "Lead with the Analytical Engines experience."},
        {"question": "What about Kubernetes?", "answer": "I have not worked with Kubernetes yet.", "use": "Acknowledge the gap honestly."},
    ]
}
ALL_VALID_REPORT = {
    "verdicts": [
        {"question": "Tell me about your Python experience.", "valid": True, "issues": []},
        {"question": "What about Kubernetes?", "valid": True, "issues": []},
    ],
    "summary": "All answers grounded.",
}
ONE_BLOCKED_REPORT = {
    "verdicts": [
        {"question": "Tell me about your Python experience.", "valid": True, "issues": []},
        {"question": "What about Kubernetes?", "valid": False, "issues": ["Invented Kubernetes experience"]},
    ],
    "summary": "One answer fabricated experience.",
}


class MockInterviewClient:
    def __init__(self, prep=PREP, report=ALL_VALID_REPORT):
        self.prep = prep
        self.report = report
        self.calls = []

    def generate_interview_questions(self, resume, job):
        self.calls.append(("generate", resume, job))
        return self.prep

    def validate_interview(self, resume, job, interview_prep):
        self.calls.append(("validate", resume, job, interview_prep))
        return self.report


class InterviewQuestionsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.temp_dir.name) / "resume_builder.db"
        initialize_database()
        person_id = create_person("Ada Lovelace", email="ada@example.com")
        self.resume_id = create_resume(
            person_id,
            "Ada Resume",
            raw_text=RESUME_JSON["raw_text"],
            resume_json=RESUME_JSON,
        )
        self.job_id = add_job(
            "Data Engineer",
            "Required: Python and SQL\nPreferred: Docker",
            "Engineering",
            company_name="Analytical Engines",
            min_years_experience=2,
            max_years_experience=5,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_endpoint_returns_questions_with_answers(self):
        client = MockInterviewClient()
        with patch("src.app.main.create_model_client", return_value=client):
            response = interview_questions(self.job_id, resume_id=None)

        self.assertEqual(response["jobId"], str(self.job_id))
        self.assertEqual(response["jobTitle"], "Data Engineer")
        self.assertEqual(response["company"], "Analytical Engines")
        self.assertEqual(response["category"], "Engineering")
        self.assertEqual(len(response["questions"]), 2)
        self.assertEqual(response["blocked"], [])
        self.assertEqual(response["questions"][0]["question"], PREP["questions"][0]["question"])
        self.assertEqual(response["questions"][0]["answer"], PREP["questions"][0]["answer"])
        self.assertEqual(response["questions"][0]["use"], PREP["questions"][0]["use"])
        generated_resume = client.calls[0][1]
        self.assertEqual(generated_resume["name"], "Ada Lovelace")
        self.assertIn("Python", generated_resume["skills"])

    def test_endpoint_blocks_invalid_question(self):
        client = MockInterviewClient(report=ONE_BLOCKED_REPORT)
        with patch("src.app.main.create_model_client", return_value=client):
            response = interview_questions(self.job_id, resume_id=None)

        self.assertEqual(len(response["questions"]), 1)
        self.assertEqual(response["questions"][0]["question"], PREP["questions"][0]["question"])
        self.assertEqual(len(response["blocked"]), 1)
        self.assertEqual(response["blocked"][0]["question"], PREP["questions"][1]["question"])
        self.assertIn("Invented Kubernetes experience", response["blocked"][0]["reason"])

    def test_endpoint_falls_back_to_latest_resume(self):
        person_id = create_person("Grace Hopper", email="grace@example.com")
        create_resume(person_id, "Grace Resume", raw_text=RESUME_JSON_2["raw_text"], resume_json=RESUME_JSON_2)
        client = MockInterviewClient()
        with patch("src.app.main.create_model_client", return_value=client):
            response = interview_questions(self.job_id, resume_id=None)

        generated_resume = client.calls[0][1]
        self.assertEqual(generated_resume["name"], "Grace Hopper")

    def test_endpoint_uses_explicit_resume_id(self):
        person_id = create_person("Grace Hopper", email="grace@example.com")
        second_id = create_resume(person_id, "Grace Resume", raw_text=RESUME_JSON_2["raw_text"], resume_json=RESUME_JSON_2)
        client = MockInterviewClient()
        with patch("src.app.main.create_model_client", return_value=client):
            response = interview_questions(self.job_id, resume_id=second_id)

        generated_resume = client.calls[0][1]
        self.assertEqual(generated_resume["name"], "Grace Hopper")

    def test_missing_job_returns_not_found(self):
        with self.assertRaises(HTTPException):
            interview_questions(999)

    def test_missing_resume_returns_not_found(self):
        with self.assertRaises(HTTPException):
            interview_questions(self.job_id, resume_id=999)

    def test_wrapper_rejects_malformed_generator_output(self):
        client = MockInterviewClient(prep={"questions": [{"question": "Q", "use": "U"}]})
        with self.assertRaises(ValidationError):
            generate_interview_questions(RESUME_JSON, parse_job({"job_title": "Data Engineer", "job_description": "Python"}), client)

    def test_wrapper_validates_report_shape(self):
        client = MockInterviewClient(report={"verdicts": [{"valid": True}]})
        with self.assertRaises(ValidationError):
            validate_interview(RESUME_JSON, parse_job({"job_title": "Data Engineer", "job_description": "Python"}), InterviewPrep.model_validate(PREP), client)


if __name__ == "__main__":
    unittest.main()
