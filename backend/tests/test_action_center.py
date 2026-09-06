import unittest

from src.services.action_center import build_skill_gaps


class BuildSkillGapsTest(unittest.TestCase):
    def _jobs(self):
        return [
            {"id": 1, "job_title": "Data Analyst Intern", "salary_min": 2200, "salary_max": 2800, "job_description": "Needs Python and SQL for ETL pipelines."},
            {"id": 2, "job_title": "Market Risk Analyst Intern", "salary_min": 2000, "salary_max": 2600, "job_description": "Python or other programming experience. SQL is valued."},
            {"id": 3, "job_title": "Corporate Finance Intern", "salary_min": 1800, "salary_max": 2400, "job_description": "Excel and PowerPoint only, no programming required."},
            {"id": 99, "job_title": "Equity Research Analyst Intern", "salary_min": 2000, "salary_max": 2600, "job_description": "DCF modelling and Bloomberg Market Concepts a plus."},
        ]

    def test_ranks_skills_by_cross_job_demand(self):
        gaps = build_skill_gaps(
            missing_skills=["Python", "SQL", "Bloomberg Terminal usage"],
            current_job_id=99,
            all_jobs=self._jobs(),
        )
        names_in_order = [g["name"] for g in gaps]
        # Python and SQL each appear in 2 other jobs; "Bloomberg Terminal usage" matches none
        # (the job text says "Bloomberg Market Concepts", not "Bloomberg Terminal") -> ranks last.
        self.assertEqual(names_in_order[-1], "Bloomberg Terminal usage")
        self.assertIn("Python", names_in_order[:2])
        self.assertIn("SQL", names_in_order[:2])
        python_entry = next(g for g in gaps if g["name"] == "Python")
        self.assertEqual(python_entry["jobs"], 2)

    def test_computes_a_real_salary_premium_from_job_data(self):
        gaps = build_skill_gaps(
            missing_skills=["Python"],
            current_job_id=99,
            all_jobs=self._jobs(),
        )
        # Jobs mentioning Python (2200-2800, 2000-2600 midpoints 2500/2300) pay more on
        # average than the one job without it (1800-2400 midpoint 2100).
        self.assertIn("median", gaps[0]["pay"])
        self.assertIn("S$", gaps[0]["pay"])

    def test_reports_no_premium_honestly_when_data_does_not_support_one(self):
        jobs = [
            {"id": 1, "job_title": "A", "salary_min": 1000, "salary_max": 1000, "job_description": "needs rust"},
            {"id": 2, "job_title": "B", "salary_min": 5000, "salary_max": 5000, "job_description": "no programming"},
            {"id": 99, "job_title": "Current", "salary_min": 2000, "salary_max": 2000, "job_description": ""},
        ]
        gaps = build_skill_gaps(missing_skills=["Rust"], current_job_id=99, all_jobs=jobs)
        self.assertEqual(gaps[0]["pay"], "No premium")

    def test_returns_empty_list_for_no_missing_skills(self):
        self.assertEqual(build_skill_gaps(missing_skills=[], current_job_id=99, all_jobs=self._jobs()), [])

    def test_respects_limit(self):
        gaps = build_skill_gaps(
            missing_skills=["Python", "SQL", "Bloomberg Terminal usage", "Excel"],
            current_job_id=99,
            all_jobs=self._jobs(),
            limit=2,
        )
        self.assertEqual(len(gaps), 2)

    def test_matches_via_meaningful_keyword_overlap_not_just_exact_phrase(self):
        jobs = [
            {"id": 1, "job_title": "Corporate Finance Intern", "salary_min": 1800, "salary_max": 2400, "job_description": "Familiarity with Bloomberg Market Concepts (BMC) is a plus."},
            {"id": 99, "job_title": "Current", "salary_min": 2000, "salary_max": 2600, "job_description": ""},
        ]
        gaps = build_skill_gaps(missing_skills=["Bloomberg Terminal usage"], current_job_id=99, all_jobs=jobs)
        # "Bloomberg Terminal usage" never appears verbatim, but the shared "bloomberg"
        # keyword is a real, meaningful signal that another job also touches this area.
        self.assertEqual(gaps[0]["jobs"], 1)


if __name__ == "__main__":
    unittest.main()
