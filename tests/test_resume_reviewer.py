import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.resume_intake import ResumeIntakeService
from medical_career_agent.services.resume_reviewer import ResumeReviewService


class ResumeReviewerTest(unittest.TestCase):
    def setUp(self):
        self.intake = ResumeIntakeService().analyze(
            resume_text="负责课题文献检索，使用PubMed筛选120篇文献。",
            jd_text="负责医学文献检索；要求GCP经验",
        )
        self.reviewer = ResumeReviewService()

    def test_flags_unconfirmed_numbers_and_upgraded_responsibility(self):
        result = self.reviewer.review(
            intake=self.intake,
            final_resume_text="主导课题文献检索，筛选500篇文献。",
        )
        codes = {item.code for item in result.findings}
        self.assertIn("unconfirmed_number", codes)
        self.assertIn("responsibility_upgrade", codes)
        self.assertEqual(result.unproven_requirement_ids, ("req-02",))

    def test_known_facts_do_not_create_a_warning(self):
        result = self.reviewer.review(
            intake=self.intake,
            final_resume_text="负责课题文献检索，使用PubMed筛选120篇文献。",
        )
        self.assertNotIn("unconfirmed_number", {item.code for item in result.findings})


if __name__ == "__main__":
    unittest.main()
