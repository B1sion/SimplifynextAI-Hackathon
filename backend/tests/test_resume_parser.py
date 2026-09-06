import unittest

from src.agents.resume_parser import parse_resume


class ResumeParserTest(unittest.TestCase):
    def test_parses_contact_sections_and_skills(self):
        parsed = parse_resume(
            """Ada Lovelace
ada@example.com | https://linkedin.com/in/ada

Experience
Analytical Engineer | Analytical Engines
Built an engine

Education
University of London | BSc Mathematics

Projects
Engine - A calculation engine

Skills
Python, SQL | Data analysis
"""
        )

        self.assertEqual(parsed["name"], "Ada Lovelace")
        self.assertEqual(parsed["email"], "ada@example.com")
        self.assertEqual(parsed["linkedin_url"], "https://linkedin.com/in/ada")
        self.assertEqual(parsed["work_experience"][0]["company_name"], "Analytical Engines")
        self.assertEqual(parsed["education"][0]["institution"], "University of London")
        self.assertEqual(parsed["projects"][0]["project_name"], "Engine")
        self.assertEqual(parsed["skills"], ["Python", "SQL", "Data analysis"])


if __name__ == "__main__":
    unittest.main()