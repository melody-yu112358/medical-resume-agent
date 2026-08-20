import unittest

from medical_resume_agent.api import create_app
from medical_resume_agent.services.resume_intake import ResumeIntakeService


class ResumeAgentTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app(load_model_from_environment=False).test_client()
        self.resume = "2024.01-2024.06  医院  实习生\n• 完成临床轮转并撰写 3 篇科普内容"
        self.jd = "负责医学文献检索与内容撰写，要求具备临床理解和沟通能力。"

    def test_intake_and_fallback_rewrite(self):
        intake = self.client.post("/api/resume-intake", json={"resume_text": self.resume, "jd_text": self.jd})
        self.assertEqual(intake.status_code, 200)
        self.assertTrue(intake.json["evidence_matches"])
        rewrite = self.client.post("/api/resume-rewrites", json={"resume_text": self.resume, "jd_text": self.jd})
        self.assertEqual(rewrite.status_code, 200)
        self.assertEqual(rewrite.json["mode"], "evidence_preserving_fallback")

    def test_review_flags_unconfirmed_number(self):
        response = self.client.post("/api/resume-reviews", json={
            "resume_text": self.resume, "jd_text": self.jd,
            "final_resume_text": "主导 99 场医学活动",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("unconfirmed_number", [item["code"] for item in response.json["findings"]])

    def test_empty_text_is_rejected(self):
        response = self.client.post("/api/resume-intake", json={"resume_text": "", "jd_text": self.jd})
        self.assertEqual(response.status_code, 400)


class ResumeIntakeUnitTest(unittest.TestCase):
    def test_questions_are_bounded(self):
        result = ResumeIntakeService().analyze(
            resume_text="临床轮转", jd_text="\n".join(f"要求第{i}项能力" for i in range(12))
        )
        self.assertLessEqual(len(result.questions), 8)
