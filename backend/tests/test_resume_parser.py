import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.agents.resume_parser import extract_pdf_text, parse_resume


class ResumeParserTest(unittest.TestCase):
    @patch("src.agents.resume_parser.PdfReader")
    def test_pdf_extraction_preserves_layout(self, reader_class):
        page = Mock()
        page.extract_text.return_value = "WORK EXPERIENCE\nING Bank July 2026 - December 2026\nMarket Risk Intern"
        reader_class.return_value.pages = [page]

        text = extract_pdf_text(Path("resume.pdf"))

        page.extract_text.assert_called_once_with(extraction_mode="layout")
        self.assertEqual(len(parse_resume(text)["work_experience"]), 1)

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

    def test_parses_resume_headers_with_date_ranges_and_alias_sections(self):
        parsed = parse_resume(
            """EMMANUEL NG
www.linkedin.com/in/emmanuel-ng | https://github.com/example

Education
National University of Singapore Aug 2024 - May 2028
Bachelor of Science (Hons)
Primary Major Data Science

Work Experience
ING Bank July 2026 – December 2026
Market Risk Management Intern
Executed risk reporting

Education Experience
Independent August 2025–November 2025
Project Manager
Built a model

Other Experiences
Ministry of Education January 2022 - March 2022
Teaching Intern
"""
        )

        self.assertEqual(parsed["linkedin_url"], "www.linkedin.com/in/emmanuel-ng")
        self.assertEqual(parsed["education"][0]["institution"], "National University of Singapore")
        self.assertEqual(parsed["education"][0]["degree"], "Bachelor of Science (Hons)")
        self.assertEqual(len(parsed["work_experience"]), 3)
        self.assertEqual(parsed["work_experience"][0]["company_name"], "ING Bank")
        self.assertEqual(parsed["work_experience"][0]["job_title"], "Market Risk Management Intern")
        self.assertEqual(parsed["work_experience"][0]["start_date"], "July 2026")
        self.assertEqual(parsed["work_experience"][1]["company_name"], "Independent")

    def test_parses_replacement_character_between_date_ranges(self):
        parsed = parse_resume(
            """Work Experience
ING Bank July 2026 ? December 2026
Market Risk Management Intern
"""
        )

        self.assertEqual(len(parsed["work_experience"]), 1)
        self.assertEqual(parsed["work_experience"][0]["company_name"], "ING Bank")
        self.assertEqual(parsed["work_experience"][0]["end_date"], "December 2026")

        def test_preserves_wrapped_experience_bullets(self):
                parsed = parse_resume(
                        """Work Experience
ING Bank July 2026 - December 2026
Market Risk Intern
● Monitored market risk metrics across trading books and
    banking books.
"""
                )

                self.assertEqual(parsed["work_experience"][0]["bullets"], ["Monitored market risk metrics across trading books and banking books."])


if __name__ == "__main__":
    unittest.main()