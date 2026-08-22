import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.resume_intake import ResumeIntakeService
from medical_career_agent.services.resume_rewriter import (
    ResumeRewriteRejectedError,
    ResumeRewriteService,
    evidence_preserving_rewrite,
)


class ResumeRewriterTest(unittest.TestCase):
    def setUp(self):
        self.intake = ResumeIntakeService().analyze(
            resume_text="负责课题文献检索，使用PubMed筛选120篇文献。参与组会汇报。",
            jd_text="负责医学文献检索与解读；要求跨团队沟通能力",
        )

    def test_grounded_rewrite_returns_comparison_and_reason(self):
        class GroundedModel:
            def generate(self, *, task, context):
                return '''{"items":[{"requirement_id":"req-01","source_quote":"负责课题文献检索，使用PubMed筛选120篇文献","rewritten":"使用PubMed完成课题文献检索与筛选，共处理120篇文献","reason":"突出检索工具、行动和可核实规模，对应JD的文献检索要求"}]}'''

        result = ResumeRewriteService(GroundedModel()).rewrite(intake=self.intake)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].source_quote, "负责课题文献检索，使用PubMed筛选120篇文献")
        self.assertIn("120", result.items[0].rewritten)
        self.assertIn("source_quote_is_verbatim", result.quality_checks)

    def test_invented_number_is_rejected(self):
        class InventedNumberModel:
            def generate(self, *, task, context):
                return '''{"items":[{"requirement_id":"req-01","source_quote":"负责课题文献检索，使用PubMed筛选120篇文献","rewritten":"使用PubMed筛选500篇文献","reason":"更量化"}]}'''

        with self.assertRaisesRegex(ResumeRewriteRejectedError, "unconfirmed number"):
            ResumeRewriteService(InventedNumberModel()).rewrite(intake=self.intake)

    def test_upgraded_responsibility_is_rejected(self):
        class UpgradedModel:
            def generate(self, *, task, context):
                return '''{"items":[{"requirement_id":"req-01","source_quote":"负责课题文献检索，使用PubMed筛选120篇文献","rewritten":"主导课题文献检索并筛选120篇文献","reason":"强化职责"}]}'''

        with self.assertRaisesRegex(ResumeRewriteRejectedError, "upgraded responsibility"):
            ResumeRewriteService(UpgradedModel()).rewrite(intake=self.intake)

    def test_fallback_keeps_only_verbatim_evidence_when_no_model_is_configured(self):
        result = evidence_preserving_rewrite(self.intake)
        self.assertEqual(result.mode, "evidence_preserving_fallback")
        self.assertEqual(result.items[0].rewritten, result.items[0].source_quote)
        self.assertIn("模型", result.notice)


if __name__ == "__main__":
    unittest.main()

