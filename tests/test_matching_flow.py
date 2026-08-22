import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.adapters.json_job_repository import JsonJobRepository
from medical_career_agent.application.orchestrator import CareerTransitionAgent


class MatchingFlowTest(unittest.TestCase):
    def setUp(self):
        jobs = JsonJobRepository(ROOT / "data" / "jobs.sample.json")
        self.agent = CareerTransitionAgent(jobs)

    def test_resume_to_job_match_is_traceable_and_deterministic(self):
        resume = (ROOT / "tests" / "fixtures" / "resume.sample.txt").read_text(
            encoding="utf-8"
        )
        first = self.agent.match_resume(
            resume_text=resume,
            job_id="synthetic-medical-affairs-sh-001",
        )
        second = self.agent.match_resume(
            resume_text=resume,
            job_id="synthetic-medical-affairs-sh-001",
        )

        self.assertEqual(first.report, second.report)
        self.assertGreater(first.report.score, 0)
        self.assertTrue(first.report.supporting_evidence)
        self.assertIn("evaluate_evidence", first.trace)
        self.assertTrue(any("合成测试数据" in x for x in first.report.cautions))
        self.assertIn("criterion_scores", first.report.to_dict())
        self.assertGreaterEqual(first.report.weighted_score, first.report.score)

    def test_empty_resume_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "resume_text"):
            self.agent.match_resume(
                resume_text=" ", job_id="synthetic-medical-affairs-sh-001"
            )


if __name__ == "__main__":
    unittest.main()
