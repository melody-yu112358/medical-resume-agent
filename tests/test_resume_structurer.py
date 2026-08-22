import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.resume_structurer import ResumeStructurer


class ResumeStructurerTest(unittest.TestCase):
    def setUp(self):
        self.structurer = ResumeStructurer()

    def test_groups_medical_sections_without_date_led_experience_assumptions(self):
        result = self.structurer.structure(
            resume_text="""教育背景
示例医学院 临床医学硕士
科研经历
负责队列研究的文献检索与数据清理
论文 / 学术成果
共同第一作者论文 1 篇
英语能力
CET-6 580 分"""
        )
        self.assertEqual(
            [section.section_key for section in result.sections],
            ["education", "research_experience", "publications", "languages"],
        )
        self.assertEqual(result.sections[1].lines, ("负责队列研究的文献检索与数据清理",))
        self.assertEqual(result.evidence[0].status, "extracted")
        self.assertFalse(result.unclassified_lines)

    def test_keeps_unknown_lines_for_user_confirmation(self):
        result = self.structurer.structure(resume_text="个人兴趣：跑步\n教育背景\n示例医学院")
        self.assertEqual(result.unclassified_lines, ("个人兴趣：跑步",))
        self.assertTrue(any("未归类" in question for question in result.confirmation_questions))

    def test_recognizes_existing_resume_beta_compound_research_heading(self):
        result = self.structurer.structure(
            resume_text="科研 / 实践经历\n完成临床研究文献检索"
        )
        self.assertEqual(result.sections[0].section_key, "research_experience")
        self.assertEqual(result.sections[0].lines, ("完成临床研究文献检索",))

    def test_recognizes_common_english_headings_without_translating_content(self):
        result = self.structurer.structure(
            resume_text="""Education Background
Example Medical School, M.Med.
Clinical Rotations
Completed rotations in cardiology.
Selected Publications
First-author article under review.
Languages
English: IELTS 7.0"""
        )
        self.assertEqual(
            [section.section_key for section in result.sections],
            ["education", "clinical_experience", "publications", "languages"],
        )
        self.assertEqual(result.sections[1].lines, ("Completed rotations in cardiology.",))

    def test_empty_resume_is_rejected(self):
        with self.assertRaises(ValueError):
            self.structurer.structure(resume_text="  ")
