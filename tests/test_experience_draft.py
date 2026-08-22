import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.experience_draft import ExperienceDraftService


class ExperienceDraftServiceTest(unittest.TestCase):

    def setUp(self):
        self.service = ExperienceDraftService()

    def test_draft_requires_consent(self):
        """Should require consent confirmation."""
        with self.assertRaises(ValueError):
            self.service.draft(experience_text="test", consent_confirmed=False)

    def test_draft_requires_non_empty_text(self):
        """Should require non-empty experience text."""
        with self.assertRaises(ValueError):
            self.service.draft(experience_text="", consent_confirmed=True)

    def test_meta_analysis_extraction(self):
        """Should correctly extract Meta analysis facts."""
        draft = self.service.draft(
            experience_text="在课题组参与Meta分析，负责文献检索和筛选",
            consent_confirmed=True
        )

        # Check extracted facts
        facts = draft.extracted_facts
        self.assertEqual(facts["context"]["domain"], "clinical_research")
        self.assertEqual(facts["context"]["setting"], "research_project")
        self.assertEqual(facts["role"]["responsibility_level"], "participated")
        self.assertIn("retrieve_literature", facts["actions"])
        self.assertIn("screen_studies", facts["actions"])
        self.assertIn("meta_analysis", facts["methods"])
        self.assertIn("medical_literature", facts["objects"])
        # Note: clinical_studies is not extracted because the input text doesn't mention clinical studies explicitly

        # Check unknowns
        self.assertIn("database_count", draft.unknown_items)
        self.assertIn("screening_criteria", draft.unknown_items)
        self.assertIn("study_count", draft.unknown_items)

        # Check clarifying questions (limited to 3)
        self.assertEqual(len(draft.clarifying_questions), 3)
        self.assertIn("使用了哪些数据库进行文献检索？", draft.clarifying_questions)
        self.assertIn("筛选标准是什么（如PRISMA）？", draft.clarifying_questions)
        self.assertIn("最终纳入了多少篇研究？", draft.clarifying_questions)

        # Check value angles
        self.assertTrue(any("循证研究方法" in angle for angle in draft.possible_value_angles))
        self.assertTrue(any("文献检索能力" in angle for angle in draft.possible_value_angles))

    def test_clinical_trial_extraction(self):
        """Should correctly extract clinical trial facts."""
        draft = self.service.draft(
            experience_text="参与临床试验的随访工作，负责数据收集和录入",
            consent_confirmed=True
        )

        facts = draft.extracted_facts
        self.assertEqual(facts["context"]["domain"], "clinical_research")
        self.assertEqual(facts["context"]["setting"], "clinical_trial")
        self.assertIn("clinical_studies", facts["objects"])

    def test_wet_lab_extraction(self):
        """Should correctly extract wet lab facts."""
        draft = self.service.draft(
            experience_text="在实验室进行细胞培养和qPCR实验",
            consent_confirmed=True
        )

        facts = draft.extracted_facts
        self.assertEqual(facts["context"]["domain"], "wet_lab")
        self.assertEqual(facts["context"]["setting"], "lab_experiment")

    def test_data_analysis_extraction(self):
        """Should correctly extract data analysis facts."""
        draft = self.service.draft(
            experience_text="使用R语言进行数据分析和统计建模",
            consent_confirmed=True
        )

        facts = draft.extracted_facts
        self.assertEqual(facts["context"]["domain"], "data_analysis")
        self.assertIn("r", facts["tools"])
        self.assertIn("perform_analysis", facts["actions"])

    def test_risk_flags_identification(self):
        """Should identify potential risks."""
        # Test responsibility upgrade risk
        draft1 = self.service.draft(
            experience_text="负责Meta分析的文献检索工作",
            consent_confirmed=True
        )
        self.assertTrue(any("可能存在责任等级升级风险" in flag for flag in draft1.risk_flags))

        # Test short description risk
        draft2 = self.service.draft(
            experience_text="做实验",
            consent_confirmed=True
        )
        self.assertTrue(any("描述过于简短" in flag for flag in draft2.risk_flags))

    def test_context_hint_usage(self):
        """Should use context hint when no patterns match."""
        draft = self.service.draft(
            experience_text="参与研究工作",
            context_hint="临床研究",
            consent_confirmed=True
        )
        self.assertEqual(draft.extracted_facts["context"]["domain"], "clinical_research")

    def test_output_structure(self):
        """Should return properly structured output."""
        draft = self.service.draft(
            experience_text="在课题组参与Meta分析，负责文献检索和筛选",
            consent_confirmed=True
        )

        # Check that all required fields are present
        self.assertIsInstance(draft.extracted_facts, dict)
        self.assertIsInstance(draft.unknown_items, list)
        self.assertIsInstance(draft.possible_value_angles, list)
        self.assertIsInstance(draft.clarifying_questions, list)
        self.assertIsInstance(draft.risk_flags, list)

        # Check that questions are limited to 3
        self.assertLessEqual(len(draft.clarifying_questions), 3)

        # Check to_dict method
        draft_dict = draft.to_dict()
        self.assertIsInstance(draft_dict, dict)
        self.assertIn("extracted_facts", draft_dict)
        self.assertIn("unknown_items", draft_dict)
        self.assertIn("possible_value_angles", draft_dict)
        self.assertIn("clarifying_questions", draft_dict)
        self.assertIn("risk_flags", draft_dict)


if __name__ == "__main__":
    unittest.main()