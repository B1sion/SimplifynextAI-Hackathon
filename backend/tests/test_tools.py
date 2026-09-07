import tempfile
import unittest
from pathlib import Path

from database import database
from database.database import initialize_database
from src.Tools.education_project_tools import add_education, add_project, delete_education, delete_project, update_education, update_project
from src.Tools.evaluation_tools import get_latest_evaluation, save_evaluation
from src.Tools.job_tools import add_job, delete_job, get_job, update_job
from src.Tools.optimization_tools import (
    create_optimization_run,
    create_resume_version,
    get_optimization_context,
)
from src.Tools.person_tools import create_person, get_person, update_person
from src.Tools.plan_tools import save_rewrite_plan
from src.Tools.resume_tools import create_resume, get_full_resume
from src.Tools.skill_tools import add_skill_to_resume, create_skill, get_resume_skills, remove_skill_from_resume
from src.Tools.work_experience_tools import add_experience_bullet, add_work_experience, delete_experience_bullet, delete_work_experience, update_experience_bullet, update_work_experience


class ToolLayerTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DATABASE_PATH = Path(self.temp_dir.name) / "resume_builder.db"
        initialize_database()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_resume_optimization_flow(self):
        person_id = create_person("Ada Lovelace", email="ada@example.com")
        job_id = add_job("Engineer", "Build things", company_name="Analytical Engines", category="Engineering")
        resume_id = create_resume(person_id, "Ada Resume", raw_text="Python and analysis")
        experience_id = add_work_experience(resume_id, "Analytical Engines", "Engineer")
        add_experience_bullet(experience_id, "Built an engine")
        add_education(resume_id, "University", degree="BSc")
        add_project(resume_id, "Engine", description="A project")
        skill_id = create_skill("Python", "programming_language")
        add_skill_to_resume(resume_id, skill_id, confidence=1.0, evidence="Python")

        run = create_optimization_run(resume_id, job_id)
        version = create_resume_version(run["id"], {"summary": "Engineer"})
        evaluation = save_evaluation(run["id"], version["id"], 0, 74, {"matched_skills": ["Python"]})
        save_rewrite_plan(run["id"], evaluation["id"], version["id"], 0, {"changes": []})

        self.assertEqual(get_person(person_id)["name"], "Ada Lovelace")
        self.assertEqual(get_job(job_id)["job_title"], "Engineer")
        self.assertEqual(get_full_resume(resume_id)["skills"][0]["name"], "Python")
        self.assertEqual(get_latest_evaluation(run["id"])["evaluation_json"]["matched_skills"], ["Python"])
        self.assertEqual(get_optimization_context(run["id"])["latest_plan"]["plan_json"], {"changes": []})

    def test_job_category_is_required(self):
        with self.assertRaises(TypeError):
            add_job("Engineer", "Build things")
        with self.assertRaises(ValueError):
            add_job("Engineer", "Build things", " ")

        with database.get_connection() as connection:
            columns = connection.execute("PRAGMA table_info(jobs)").fetchall()
            category = next(column for column in columns if column[1] == "category")
            self.assertEqual(category[3], 1)

    def test_crud_updates_and_deletes_nested_resume_data(self):
        person_id = create_person("Ada Lovelace")
        self.assertEqual(update_person(person_id, email="ada@example.com")["email"], "ada@example.com")
        resume_id = create_resume(person_id, "Ada Resume")
        experience_id = add_work_experience(resume_id, "Analytical Engines", "Engineer")
        bullet_id = add_experience_bullet(experience_id, "Built an engine")
        self.assertEqual(update_work_experience(experience_id, job_title="Senior Engineer")["job_title"], "Senior Engineer")
        self.assertEqual(update_experience_bullet(bullet_id, bullet_text="Built a calculation engine")["bullet_text"], "Built a calculation engine")
        self.assertTrue(delete_experience_bullet(bullet_id))
        self.assertTrue(delete_work_experience(experience_id))

        education_id = add_education(resume_id, "University", degree="BSc")
        project_id = add_project(resume_id, "Engine")
        self.assertEqual(update_education(education_id, degree="MSc")["degree"], "MSc")
        self.assertEqual(update_project(project_id, description="A project")["description"], "A project")
        self.assertTrue(delete_education(education_id))
        self.assertTrue(delete_project(project_id))

    def test_skill_upsert_validation_and_removal(self):
        person_id = create_person("Ada Lovelace")
        resume_id = create_resume(person_id, "Ada Resume")
        skill_id = create_skill("Python", "language")
        add_skill_to_resume(resume_id, skill_id, confidence=1.0, evidence="Python")
        add_skill_to_resume(resume_id, skill_id, source="inferred", confidence=0.8, evidence="Built scripts")
        self.assertEqual(get_resume_skills(resume_id)[0]["source"], "inferred")
        with self.assertRaises(ValueError):
            add_skill_to_resume(resume_id, skill_id, source="unknown")
        self.assertTrue(remove_skill_from_resume(resume_id, skill_id))
        self.assertFalse(remove_skill_from_resume(resume_id, skill_id))

    def test_job_update_and_delete(self):
        job_id = add_job("Engineer", "Build things", "Engineering")
        self.assertEqual(update_job(job_id, job_title="Senior Engineer")["job_title"], "Senior Engineer")
        self.assertTrue(delete_job(job_id))
        self.assertIsNone(get_job(job_id))


if __name__ == "__main__":
    unittest.main()
