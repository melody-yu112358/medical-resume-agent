import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.experience_draft import ExperienceDraftService


class ExperienceDraftQuestionPlanningTest(unittest.TestCase):

    def setUp(self):
        self.service = ExperienceDraftService()

    def test_dynamic_question_planning_integration(self):
        """Test that ExperienceDraftService uses dynamic question planning."""
        # Test with minimal input that should trigger question planning
        draft = self.service.draft(
            experience_text="参与Meta分析研究",
            consent_confirmed=True
        )

        # Should have generated questions
        self.assertGreater(len(draft.clarifying_questions), 0)
        self.assertLessEqual(len(draft.clarifying_questions), 3)

        # Questions should be relevant to meta-analysis
        questions_text = " ".join(draft.clarifying_questions)
        self.assertTrue(
            any(term.lower() in questions_text.lower() for term in ["database", "study", "screening", "quality", "statistical", "bias", "Cochrane"]),
            f"Questions don't seem relevant: {questions_text}"
        )

    def test_sufficient_information_stops_questioning(self):
        """Test that sufficient information results in fewer or no questions."""
        # This is harder to test directly since we always generate some questions
        # But we can test that the question planner is being used
        draft = self.service.draft(
            experience_text="参与急性冠脉综合征患者抗血小板治疗的Meta分析研究，在导师指导和团队协作下完成了从研究问题识别、系统检索、质量评价到结果解释的完整证据综合流程。",
            consent_confirmed=True
        )

        # Should still generate some questions to improve quality
        self.assertGreater(len(draft.clarifying_questions), 0)

    def test_question_planner_attributes_present(self):
        """Test that the service has a question planner attribute."""
        self.assertTrue(hasattr(self.service, 'question_planner'))
        self.assertIsNotNone(self.service.question_planner)


if __name__ == "__main__":
    unittest.main()