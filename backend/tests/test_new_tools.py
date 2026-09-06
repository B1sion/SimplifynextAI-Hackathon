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
