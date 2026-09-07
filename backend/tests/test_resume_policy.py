import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from src.services.resume_policy import omit_low_gpa
from src.services.resume_renderer import RESUME_TEMPLATE_PATH, render_resume_pdf


class ResumePolicyTest(unittest.TestCase):
    def test_omits_gpa_below_first_class_threshold(self):
        education = omit_low_gpa([
            {"institution": "University", "gpa": "3.2/4.0"},
            {"institution": "College", "grade": "4.6/5"},
            {"institution": "School", "GPA": "3.5/4"},
        ])

        self.assertNotIn("gpa", education[0])
        self.assertEqual(education[1]["grade"], "4.6/5")
        self.assertEqual(education[2]["GPA"], "3.5/4")

    def test_renderer_uses_template_order_and_contact_line(self):
        with tempfile.TemporaryDirectory() as directory:
            output = render_resume_pdf(
                {
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "linkedin_url": "linkedin.com/ada",
                    "github_url": "github.com/ada",
                    "portfolio_url": "ada.example.com",
                    "education": [
                        {"institution": "University", "degree": "BSc", "gpa": "3.2/4"},
                    ],
                    "work_experience": [{"company_name": "Company", "job_title": "Role", "start_date": "December 2025", "end_date": "January 2026", "bullets": ["Did work"]}],
                    "projects": [{"project_name": "Research", "bullets": ["Built a model"]}],
                    "skills": ["Python"],
                },
                1,
                1,
                Path(directory),
            )
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(output)).pages)

        self.assertTrue(RESUME_TEMPLATE_PATH.is_file())
        compact = " ".join(text.split())
        self.assertIn("Ada Lovelace ada@example.com | linkedin.com/ada | github.com/ada | ada.example.com", compact)
        self.assertNotIn("3.2/4", compact)
        self.assertIn("Dec 2025 - Jan 2026", compact)
        self.assertLess(compact.index("EDUCATION"), compact.index("LEADERSHIP & ACTIVITIES"))
        self.assertLess(compact.index("LEADERSHIP & ACTIVITIES"), compact.index("SKILLS & INTERESTS"))


if __name__ == "__main__":
    unittest.main()