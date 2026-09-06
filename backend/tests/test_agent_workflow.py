import os
import base64
import unittest

from src.agents.resume_agents.agentcore_client import AgentCoreClient
from src.agents.resume_agents.bedrock_client import BedrockClientError, BedrockNovaClient
from src.agents.resume_agents.contracts import ATSReport, JobIR, ResumeIR, RewritePlan
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job
from src.agents.resume_agents.planner import plan_resume
from src.agents.resume_agents.validator import validate_resume
from src.agents.resume_agents.writer import rewrite_resume


RESUME = {
    "name": "Ada Lovelace",
    "raw_text": "Python developer with data analysis experience.",
    "skills": ["Python", "SQL"],
    "work_experience": [{"company_name": "Analytical Engines", "job_title": "Engineer", "description": "Built data systems."}],
}
JOB = JobIR(title="Data Engineer", original_description="Seeking Python and SQL experience.", required_skills=["Python", "SQL"])
ATS_REPORT = {
    "ats_score": 76,
    "summary": "Good technical alignment with some keyword gaps.",
    "strengths": ["Python experience"],
    "weaknesses": ["Limited cloud keywords"],
    "matched_skills": ["Python", "SQL"],
    "missing_skills": [],
    "keyword_gaps": ["AWS"],
    "experience_gaps": [],
    "ats_issues": [],
    "high_priority_improvements": ["Clarify data-system impact"],
}


class MockWorkflowClient:
    def evaluate_resume(self, resume, job):
        return ATS_REPORT

    def plan_resume(self, resume, job, evaluation):
        return {"changes": [{"target": "summary", "action": "clarify", "priority": "high", "reason": "ATS clarity", "instruction": "Clarify existing data-system evidence."}], "user_recommendations": [], "prohibited_claims": []}

    def rewrite_resume(self, resume, job, plan):
        return {**resume, "summary": "Built data systems using Python and SQL."}

    def validate_resume(self, authoritative_resume, candidate_resume):
        return {"valid": True, "summary": "Candidate is truthful"}


class FakeBedrockRuntime:
    def invoke_model(self, **kwargs):
        return {"body": FakeBody('{"output":{"message":{"content":[{"text":"```json\\n{\\"ats_score\\": 76}\\n```"}]}}}')}


class FakeBody:
    def __init__(self, content):
        self.content = content

    def read(self):
        return self.content.encode()


class AgentWorkflowTest(unittest.TestCase):
    def test_agentcore_resume_reader_receives_original_pdf_document(self):
        calls = []

        def invoke(operation, payload):
            calls.append((operation, payload))
            return {"name": "Ada Lovelace"}

        parsed = AgentCoreClient(invoke=invoke).parse_resume_pdf(b"%PDF-test", "ada.pdf")

        self.assertEqual(parsed["name"], "Ada Lovelace")
        self.assertEqual(calls[0][0], "parse_resume")
        document = calls[0][1]["document"]
        self.assertEqual(document["media_type"], "application/pdf")
        self.assertEqual(document["filename"], "ada.pdf")
        self.assertEqual(base64.b64decode(document["data_base64"]), b"%PDF-test")

    def test_structured_evaluator_planner_writer_outputs(self):
        client = MockWorkflowClient()
        report = evaluate_resume(RESUME, JOB, client)
        plan = plan_resume(RESUME, JOB, report, client)
        candidate = rewrite_resume(RESUME, JOB, plan, client)

        self.assertIsInstance(report, ATSReport)
        self.assertEqual(report.ats_score, 76)
        self.assertIsInstance(plan, RewritePlan)
        self.assertEqual(plan.changes[0].target, "summary")
        self.assertIsInstance(candidate, ResumeIR)
        self.assertIn("Python", candidate.summary)

    def test_nova_json_response_is_decoded(self):
        client = BedrockNovaClient(client=FakeBedrockRuntime(), model_id="amazon.nova-micro-v1:0")
        self.assertEqual(client.generate_json("Return JSON", {})["ats_score"], 76)

    def test_bedrock_client_rejects_non_json_model_output(self):
        with self.assertRaises(BedrockClientError):
            BedrockNovaClient._parse_json("The model did not return JSON")

    def test_job_parser_preserves_description_and_classifies_requirements(self):
        job = parse_job({"job_title": "Data Engineer", "job_description": "Required: Python and SQL\nPreferred: Docker\nBachelor degree"})
        self.assertEqual(job.title, "Data Engineer")
        self.assertIn("python", job.required_skills)
        self.assertIn("docker", job.preferred_skills)
        self.assertEqual(job.original_description, "Required: Python and SQL\nPreferred: Docker\nBachelor degree")

    def test_truthfulness_validator_rejects_fabricated_candidate(self):
        fabricated = {**RESUME, "skills": ["Python", "Kubernetes"]}
        report = validate_resume(RESUME, fabricated)
        self.assertFalse(report.valid)
        self.assertEqual(report.unsupported_additions[0].category, "invented_skill")

    def test_truthfulness_validator_rejects_changed_dates(self):
        authoritative = {**RESUME, "work_experience": [{"company_name": "Analytical Engines", "job_title": "Engineer", "start_date": "2020", "end_date": "2022"}]}
        candidate = {**authoritative, "work_experience": [{"company_name": "Analytical Engines", "job_title": "Engineer", "start_date": "2021", "end_date": "2022"}]}
        report = validate_resume(authoritative, candidate)
        self.assertFalse(report.valid)
        self.assertIn("2021", report.changed_dates)

    @unittest.skipUnless(os.getenv("RUN_LIVE_BEDROCK") == "1", "Set RUN_LIVE_BEDROCK=1 to run the live Nova test")
    def test_live_nova_evaluator(self):
        report = evaluate_resume(RESUME, JOB, BedrockNovaClient())
        self.assertIsInstance(report, ATSReport)
        self.assertGreaterEqual(report.ats_score, 0)
        self.assertLessEqual(report.ats_score, 100)

    @unittest.skipUnless(os.getenv("RUN_LIVE_BEDROCK") == "1", "Set RUN_LIVE_BEDROCK=1 to run the live Nova workflow")
    def test_live_nova_evaluator_planner_writer_evaluator(self):
        client = BedrockNovaClient()
        initial = evaluate_resume(RESUME, JOB, client)
        plan = plan_resume(RESUME, JOB, initial, client)
        candidate = rewrite_resume(RESUME, JOB, plan, client)
        validation = validate_resume(RESUME, candidate, client)
        final = evaluate_resume(candidate, JOB, client)

        self.assertIsInstance(initial, ATSReport)
        self.assertIsInstance(plan, RewritePlan)
        self.assertIsInstance(candidate, ResumeIR)
        self.assertTrue(validation.valid)
        self.assertIsInstance(final, ATSReport)
        self.assertEqual(candidate.name, RESUME["name"])
        self.assertEqual(candidate.raw_text, RESUME["raw_text"])
        self.assertEqual(candidate.skills, RESUME["skills"])
        self.assertGreaterEqual(initial.ats_score, 0)
        self.assertLessEqual(final.ats_score, 100)


if __name__ == "__main__":
    unittest.main()