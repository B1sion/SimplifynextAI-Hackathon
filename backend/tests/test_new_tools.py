import tempfile
import unittest
from pathlib import Path

from database import database
from database.database import initialize_database, get_connection
from src.Tools.person_tools import create_person
from src.Tools.job_tools import add_job
from src.Tools.profile_tools import get_profile_answers, save_profile_answers
from src.Tools.watch_tools import get_watch_settings, set_watch_enabled
from src.Tools.application_tools import create_application, get_applications_for_person


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


if __name__ == "__main__":
    unittest.main()
