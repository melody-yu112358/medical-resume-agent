import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.resume_intake import ResumeIntakeService


class ResumeIntakeTest(unittest.TestCase):
    def setUp(self):
        self.service = ResumeIntakeService()

    def test_medical_resume_and_jd_produce_traceable_front_half(self):
        result = self.service.analyze(
            resume_text=(
                "医学硕士。负责课题文献检索，使用PubMed筛选120篇文献。"
                "参与组会汇报和跨团队沟通。"
            ),
            jd_text=(
                "负责医学文献检索与解读；具备医学材料写作能力；"
                "要求良好的跨团队沟通能力；有GCP经验者优先"
            ),
        )
        self.assertEqual(len(result.requirements), 4)
        self.assertEqual(result.requirements[-1].category, "bonus")
        self.assertEqual(result.evidence_matches[0].strength, "strong")
        self.assertTrue(any(item.gap_type == "missing_evidence" for item in result.evidence_matches))
        self.assertLessEqual(len(result.questions), 8)
        self.assertEqual(result.version, "resume-intake-v0.1")

    def test_questions_are_capped_at_eight(self):
        jd = "；".join(f"要求技能{i}" for i in range(12))
        result = self.service.analyze(resume_text="医学本科", jd_text=jd)
        self.assertEqual(len(result.questions), 8)

    def test_both_inputs_are_required(self):
        with self.assertRaises(ValueError):
            self.service.analyze(resume_text="", jd_text="岗位要求")
        with self.assertRaises(ValueError):
            self.service.analyze(resume_text="医学本科", jd_text="")


if __name__ == "__main__":
    unittest.main()

