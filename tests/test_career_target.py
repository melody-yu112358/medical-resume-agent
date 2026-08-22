import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.career_target import CareerTargetService


class CareerTargetTest(unittest.TestCase):
    def test_sourced_card_becomes_resume_target(self):
        career = SimpleNamespace(
            career_id="healthcare-ai-product-manager",
            name="医疗 AI 产品经理",
            summary="连接医疗场景、用户需求与 AI 技术团队。",
            required_skills=(
                SimpleNamespace(claim="能够进行需求拆解和产品设计。", source_ids=("source-a",)),
                SimpleNamespace(claim="能够与技术团队讨论可行性。", source_ids=("source-b",)),
            ),
            review_status="draft",
        )
        target = CareerTargetService().build(career)
        self.assertEqual(target.career_name, "医疗 AI 产品经理")
        self.assertEqual(len(target.requirements), 2)
        self.assertIn("要求：能够进行需求拆解和产品设计。", target.generated_jd_text)
        self.assertEqual(target.source_ids, ("source-a", "source-b"))


if __name__ == "__main__":
    unittest.main()

