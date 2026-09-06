import os
import unittest

from src.agents.resume_agents.bedrock_client import BedrockNovaClient
from src.agents.resume_agents.contracts import ATSReport, JobIR, ResumeIR, RewritePlan
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.planner import plan_resume
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


class FakeBedrockRuntime:
    def invoke_model(self, **kwargs):
        return {"body": FakeBody('{"output":{"message":{"content":[{"text":"```json\\n{\\"ats_score\\": 76}\\n```"}]}}}')}


class FakeBody:
    def __init__(self, content):
        self.content = content

    def read(self):
        return self.content.encode()


class AgentWorkflowTest(unittest.TestCase):
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

    @unittest.skipUnless(os.getenv("RUN_LIVE_BEDROCK") == "1", "Set RUN_LIVE_BEDROCK=1 to run the live Nova test")
    def test_live_nova_evaluator(self):
        report = evaluate_resume(RESUME, JOB, BedrockNovaClient())
        self.assertIsInstance(report, ATSReport)
        self.assertGreaterEqual(report.ats_score, 0)
        self.assertLessEqual(report.ats_score, 100)


if __name__ == "__main__":
    unittest.main()