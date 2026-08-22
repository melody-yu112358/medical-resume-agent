import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.resume_translation import ResumeTranslationService


class ResumeTranslationServiceTest(unittest.TestCase):
    def test_recommends_only_confirmed_capabilities(self):
        document = {
            "schema_version": "resume-document-v1",
            "evidence": [{"evidence_id": "ev-1", "status": "user_confirmed"}],
            "capability_profile": [
                {"name": "孟德尔随机化", "category": "research_method", "evidence_ids": ["ev-1"]},
                {"name": "未确认能力", "category": "wet_lab", "evidence_ids": ["missing"]},
            ],
        }
        result = ResumeTranslationService().translate(
            resume_document=document, jd_text="临床科研博士项目，要求研究方法与统计能力", target_profile="doctoral"
        )
        self.assertEqual([item.capability for item in result.recommendations], ["孟德尔随机化"])
        self.assertEqual(result.recommendations[0].market_value, "因果推断与循证研究方法")

    def test_requires_formal_document_and_jd(self):
        service = ResumeTranslationService()
        with self.assertRaises(ValueError):
            service.translate(resume_document={}, jd_text="岗位")
        with self.assertRaises(ValueError):
            service.translate(resume_document={"schema_version": "resume-document-v1"}, jd_text="")

    def test_translates_the_same_capability_for_the_selected_market(self):
        document = {
            "schema_version": "resume-document-v1",
            "evidence": [{"evidence_id": "ev-1", "status": "user_confirmed"}],
            "capability_profile": [{
                "name": "Meta 分析", "category": "research_method", "evidence_ids": ["ev-1"],
            }],
        }
        service = ResumeTranslationService()
        doctoral = service.translate(resume_document=document, jd_text="博士研究", target_profile="doctoral")
        affairs = service.translate(resume_document=document, jd_text="医学事务", target_profile="medical_affairs")
        self.assertEqual(doctoral.recommendations[0].market_value, "因果推断与循证研究方法")
        self.assertEqual(affairs.recommendations[0].market_value, "研究证据解读能力")
