import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.profile_drafter import (  # noqa: E402
    ProfileDraftOutputRejectedError,
    ProfileDraftService,
    confirmed_profile_from_payload,
)


SOURCE_TEXT = (
    "我在研究生组会中检索并比较了十二篇临床研究，整理出结论、局限和待确认问题，"
    "随后面向不同专业的同学完成了一次二十分钟汇报并回答提问。"
)


class FakeDraftModel:
    def __init__(self, source_quote: str) -> None:
        self.source_quote = source_quote

    def generate(self, *, task, context):
        return json.dumps(
            {
                "evidence": [
                    {
                        "source_quote": self.source_quote,
                        "capabilities": ["文献检索", "证据比较"],
                        "confidence": 0.86,
                    }
                ],
                "unknowns": ["尚不清楚是否有可展示的汇报材料"],
                "follow_up_question": "你是否保留了汇报材料或收到过反馈？",
            },
            ensure_ascii=False,
        )


class ProfileDraftingTest(unittest.TestCase):
    def test_draft_keeps_grounded_quote_and_requires_confirmation(self):
        quote = "检索并比较了十二篇临床研究"
        draft = ProfileDraftService(FakeDraftModel(quote)).draft(
            education_field="临床医学",
            education_stage="硕士二年级",
            experience_text=SOURCE_TEXT,
            locations=("上海",),
            weekly_learning_hours=8,
            consent_confirmed=True,
        )

        self.assertEqual(draft.evidence[0].source_quote, quote)
        self.assertEqual(draft.evidence[0].confirmation_status, "unverified")
        self.assertFalse(draft.persisted)
        self.assertTrue(draft.consent_recorded)

    def test_draft_rejects_quote_not_found_in_user_input(self):
        service = ProfileDraftService(FakeDraftModel("我独立发表了十篇论文"))
        with self.assertRaises(ProfileDraftOutputRejectedError):
            service.draft(
                education_field="临床医学",
                education_stage="硕士二年级",
                experience_text=SOURCE_TEXT,
                consent_confirmed=True,
            )

    def test_confirmed_payload_becomes_temporary_medical_profile(self):
        profile = confirmed_profile_from_payload(
            {
                "profile_confirmed": True,
                "consent_recorded": True,
                "education": {"field": "临床医学", "stage": "硕士二年级"},
                "evidence": [
                    {
                        "source_quote": "检索并比较了十二篇临床研究",
                        "capabilities": ["文献检索", "证据比较"],
                        "confidence": 0.86,
                        "confirmed": True,
                    }
                ],
                "constraints": {
                    "locations": ["上海"],
                    "weekly_learning_hours": 8,
                    "non_negotiables": ["不接受长期高频出差"],
                },
                "unknowns": ["尚不清楚是否有可展示的汇报材料"],
            }
        )

        self.assertEqual(profile.profile_id, "session-confirmed-profile")
        self.assertEqual(profile.profile_type, "consented")
        self.assertEqual(profile.evidence[0].statement, "检索并比较了十二篇临床研究")


if __name__ == "__main__":
    unittest.main()
