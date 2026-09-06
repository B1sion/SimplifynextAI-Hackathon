import tempfile
import unittest
from pathlib import Path

from database import database
from database.database import initialize_database
from src.Tools.evaluation_tools import get_evaluations_for_run
from src.Tools.job_tools import add_job
from src.Tools.optimization_tools import get_optimization_context, get_resume_versions
from src.Tools.person_tools import create_person
from src.Tools.resume_tools import create_resume
from src.agents.resume_agents.evaluator import evaluate_resume
from src.agents.resume_agents.job_parser import parse_job
from src.services.optimization_engine import optimize_resume


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.temp_dir.name) / "resume_builder.db"
        initialize_database()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_evaluator_rejects_malformed_model_output(self):
        class MalformedClient:
            def evaluate_resume(self, resume, job):
                return []

        with self.assertRaises((TypeError, ValueError)):
            evaluate_resume({"name": "Ada"}, parse_job({"job_title": "Engineer", "job_description": "Python"}), MalformedClient())

    def test_evaluator_validates_mocked_ats_report(self):
        class MockEvaluator:
            def evaluate_resume(self, resume, job):
                self.resume = resume
                self.job = job
                return {"ats_score": 72, "summary": "Strong technical alignment", "matched_skills": ["Python"], "keyword_gaps": ["Kubernetes"]}

        client = MockEvaluator()
        report = evaluate_resume(
            {"name": "Ada", "raw_text": "Python", "skills": ["Python"]},
            parse_job({"job_title": "Engineer", "job_description": "Python"}),
            client,
        )

        self.assertEqual(report.ats_score, 72)
        self.assertEqual(report.matched_skills, ["Python"])
        self.assertEqual(report.keyword_gaps, ["Kubernetes"])

    def test_optimization_preserves_versions_and_stops_on_small_improvement(self):
        person_id = create_person("Ada Lovelace")
        resume_json = {"name": "Ada Lovelace", "raw_text": "Python", "skills": ["Python"], "work_experience": [], "education": [], "projects": []}
        resume_id = create_resume(person_id, "Ada", raw_text="Python", resume_json=resume_json)
        job_id = add_job("Engineer", "Python engineer", "Engineering")
        scores = iter([60, 74, 75])
        plans = iter([
            {"changes": [{"target": "summary", "action": "rewrite", "priority": "high", "reason": "clarity", "instruction": "Clarify existing evidence"}]},
            {"changes": [{"target": "summary", "action": "rewrite", "priority": "low", "reason": "clarity", "instruction": "Clarify existing evidence"}]},
        ])

        class MockModelClient:
            def evaluate_resume(self, resume, job):
                return {"ats_score": next(scores), "matched_skills": ["Python"]}

            def plan_resume(self, resume, job, evaluation):
                return next(plans)

            def rewrite_resume(self, resume, job, plan):
                return resume

            def validate_resume(self, authoritative_resume, candidate_resume):
                return {"valid": True, "summary": "ok"}

        result = optimize_resume(resume_id, job_id, MockModelClient())
        run_id = result["run"]["id"]
        evaluations = get_evaluations_for_run(run_id)
        versions = get_resume_versions(run_id)
        context = get_optimization_context(run_id)
        self.assertEqual([row["score"] for row in evaluations], [60, 74, 75])
        self.assertEqual([row["version_number"] for row in versions], [0, 1, 2])
        self.assertEqual(context["run"]["status"], "completed")
        self.assertEqual(context["run"]["current_score"], 75)
        rendered_path = Path(result["rendered_file_path"])
        self.assertTrue(rendered_path.is_file())
        self.assertGreater(rendered_path.stat().st_size, 0)
        rendered_path.unlink(missing_ok=True)

    def test_optimization_stops_at_target_score(self):
        person_id = create_person("Ada Lovelace")
        resume_id = create_resume(person_id, "Ada", raw_text="Python", resume_json={"name": "Ada", "raw_text": "Python", "skills": ["Python"]})
        job_id = add_job("Engineer", "Python engineer", "Engineering")

        class TargetClient:
            def evaluate_resume(self, resume, job):
                return {"ats_score": 85}

        result = optimize_resume(resume_id, job_id, TargetClient())
        self.assertEqual(len(get_evaluations_for_run(result["run"]["id"])), 1)
        self.assertEqual(result["run"]["status"], "completed")

    def test_orchestrator_retries_rejected_candidate_before_persisting(self):
        person_id = create_person("Ada Lovelace", email="ada@example.com")
        resume_id = create_resume(
            person_id,
            "Ada",
            raw_text="Python",
            resume_json={"name": "Ada Lovelace", "email": "ada@example.com", "raw_text": "Python", "skills": ["Python"]},
        )
        job_id = add_job("Engineer", "Python engineer", "Engineering")

        class RetryingClient:
            def __init__(self):
                self.plan_calls = 0
                self.rewrite_calls = 0
                self.orchestrator_calls = 0

            def evaluate_resume(self, resume, job):
                return {"ats_score": 60 if self.rewrite_calls == 0 else 80}

            def plan_resume(self, resume, job, evaluation):
                self.plan_calls += 1
                self.received_recovery = "recovery_directive" in evaluation
                return {"changes": [{"target": "summary", "priority": "high", "action": "rewrite", "instruction": "Clarify", "reason": "alignment"}]}

            def rewrite_resume(self, resume, job, plan):
                self.rewrite_calls += 1
                if self.rewrite_calls == 1:
                    return {**resume, "skills": ["Python", "Kubernetes"]}
                return {**resume, "summary": "Python engineer"}

            def validate_resume(self, authoritative_resume, candidate_resume):
                if self.rewrite_calls == 1:
                    return {
                        "valid": False,
                        "unsupported_additions": [{"category": "invented_skill", "claim": "Kubernetes", "reason": "Unsupported skill"}],
                        "summary": "Unsupported skill",
                    }
                return {"valid": True, "summary": "Candidate is truthful"}

            def orchestrate(self, state):
                self.orchestrator_calls += 1
                self.validation_report = state["validation_report"]
                return {
                    "failure_type": "writer_failure",
                    "summary": "Remove the unsupported skill and preserve the authoritative fields.",
                    "validation_failures": ["Kubernetes"],
                    "facts_to_restore": [],
                    "facts_to_preserve": ["email", "skills"],
                    "unsupported_content_to_remove": ["Kubernetes"],
                    "planner_corrections": ["Keep the rewrite limited to supported evidence."],
                    "writer_constraints": ["Preserve all untouched fields exactly."],
                    "retry_strategy": "Retry with corrected instructions.",
                }

        client = RetryingClient()
        result = optimize_resume(resume_id, job_id, client, max_iterations=1, target_score=80)

        self.assertEqual(result["run"]["status"], "completed")
        self.assertEqual(client.orchestrator_calls, 1)
        self.assertEqual(client.plan_calls, 2)
        self.assertTrue(client.received_recovery)
        self.assertEqual(len(get_resume_versions(result["run"]["id"])), 2)
        self.assertEqual([row["score"] for row in get_evaluations_for_run(result["run"]["id"])], [60, 80])
        self.assertNotIn("Kubernetes", result["resume"]["skills"])

    def test_validator_rejection_does_not_persist_candidate_version(self):
        person_id = create_person("Ada Lovelace")
        resume_id = create_resume(person_id, "Ada", raw_text="Python", resume_json={"name": "Ada", "raw_text": "Python", "skills": ["Python"]})
        job_id = add_job("Engineer", "Python engineer", "Engineering")

        class RejectingClient:
            def evaluate_resume(self, resume, job):
                return {"ats_score": 60}

            def plan_resume(self, resume, job, evaluation):
                return {"changes": [{"target": "summary", "priority": "high", "action": "rewrite", "instruction": "Rewrite", "reason": "clarity"}]}

            def rewrite_resume(self, resume, job, plan):
                return {**resume, "skills": ["Python", "Kubernetes"]}

            def validate_resume(self, authoritative_resume, candidate_resume):
                return {"valid": False, "summary": "Unsupported skill"}

        result = optimize_resume(resume_id, job_id, RejectingClient())
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(len(get_resume_versions(result["run"]["id"])), 1)

    def test_optimization_does_not_exceed_max_iterations(self):
        person_id = create_person("Ada Lovelace")
        resume_id = create_resume(person_id, "Ada", raw_text="Python", resume_json={"name": "Ada", "raw_text": "Python", "skills": ["Python"]})
        job_id = add_job("Engineer", "Python engineer", "Engineering")
        scores = iter([60, 65, 70, 75])

        class BoundedClient:
            def evaluate_resume(self, resume, job):
                return {"ats_score": next(scores)}

            def plan_resume(self, resume, job, evaluation):
                return {"changes": [{"target": "summary", "priority": "low", "action": "rewrite", "instruction": "Clarify", "reason": "clarity"}]}

            def rewrite_resume(self, resume, job, plan):
                return resume

            def validate_resume(self, authoritative_resume, candidate_resume):
                return {"valid": True}

        result = optimize_resume(resume_id, job_id, BoundedClient(), max_iterations=3, min_score_improvement=0)
        self.assertEqual(len(get_evaluations_for_run(result["run"]["id"])), 4)
        self.assertEqual(len(get_resume_versions(result["run"]["id"])), 4)


if __name__ == "__main__":
    unittest.main()