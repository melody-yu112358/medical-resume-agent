import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.api import create_app


SOURCE = "师兄带我用 R 对研究数据做敏感性分析，后来我自己完成了一部分；文献筛选由我独立完成。"


class ActivityProposalConversationTest(unittest.TestCase):
    def create(self, client):
        return client.post("/api/conversations", json={}).get_json()["session_id"]

    def post(self, client, sid, body):
        response = client.post(f"/api/conversations/{sid}/messages", json=body)
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def test_no_model_generates_manual_deterministic_proposals_and_reload_persists(self):
        client = create_app(load_model_from_environment=False).test_client()
        sid = self.create(client)
        self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})

        reloaded = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertTrue(reloaded["activity_proposals"])
        self.assertTrue(
            any(
                item["execution_mode"] in {"unknown", "supervised", "independent"}
                for item in reloaded["activity_proposals"]
            )
        )
        pending = [item["proposal_id"] for item in reloaded["activity_proposals"]]
        response = self.post(
            client, sid,
            {"action": "confirm_activity_proposals", "proposal_ids": pending},
        )
        self.assertIsNone(
            client.get(f"/api/conversations/{sid}").get_json()["state"][
                "confirmed_canonical_experience"
            ]
        )
        self.assertIn("缺少责任或范围确认", response["assistant_message"])

    def test_deterministic_activities_keep_retrieval_screening_and_r_analysis_separate(self):
        client = create_app(load_model_from_environment=False).test_client()
        sid = self.create(client)
        self.post(
            client, sid,
            {
                "text": "用 PubMed 检索文献，完成文献筛选，并用 R 做敏感性分析。",
                "consent_confirmed": True,
            },
        )

        proposals = client.get(f"/api/conversations/{sid}").get_json()["state"][
            "activity_proposals"
        ]
        by_action = {
            item["components"]["actions"][0]: item["components"] for item in proposals
        }
        self.assertEqual(by_action["retrieve_literature"]["tools"], ["pubmed"])
        self.assertFalse(by_action["screen_studies"]["tools"])
        self.assertEqual(by_action["perform_analysis"]["tools"], ["r"])
        self.assertEqual(
            by_action["perform_analysis"]["methods"], ["sensitivity_analysis"]
        )

    def test_rich_intake_binds_components_to_their_own_activity(self):
        client = create_app(load_model_from_environment=False).test_client()
        sid = self.create(client)
        response = self.post(
            client, sid,
            {
                "text": (
                    "参与系统综述和 Meta 分析，明确研究问题并制定研究方案，设计检索式，"
                    "使用 PubMed、Web of Science 和中国知网检索文献，完成文献筛选、"
                    "数据提取、质量评价和 R 统计分析，形成检索记录、筛选记录、"
                    "数据提取表、分析代码、分析图表和研究报告。"
                ),
                "consent_confirmed": True,
            },
        )

        proposals = response["state"]["activity_proposals"]
        by_action = {
            item["components"]["actions"][0]: item["components"]
            for item in proposals
        }
        self.assertEqual(
            by_action["retrieve_literature"]["tools"],
            ["pubmed", "web_of_science", "cnki"],
        )
        self.assertFalse(by_action["screen_studies"]["tools"])
        self.assertEqual(
            by_action["extract_data"]["artifacts"], []
        )
        self.assertEqual(by_action["perform_analysis"]["tools"], ["r"])
        self.assertEqual(
            by_action["perform_analysis"]["artifacts"], []
        )
        self.assertEqual(
            by_action["prepare_research_outputs"]["artifacts"],
            [
                "search_record", "screening_record", "data_extraction_sheet",
                "analysis_code", "analysis_figures", "research_report",
            ],
        )
        for action in ("define_research_question", "screen_studies", "extract_data"):
            self.assertFalse(by_action[action]["methods"])
            self.assertFalse(by_action[action]["artifacts"])

    def test_multiturn_quotes_confirm_atomically_without_partial_update(self):
        client = create_app(load_model_from_environment=False).test_client()
        sid = self.create(client)
        self.post(
            client, sid,
            {
                "action": "submit_experience",
                "text": "在导师指导下用 PubMed 检索文献。",
                "consent_confirmed": True,
            },
        )
        response = self.post(
            client, sid,
            {
                "action": "update_facts",
                "text": "我与同学共同完成文献筛选。",
                "consent_confirmed": True,
            },
        )
        pending = [
            item
            for item in response["state"]["activity_proposals"]
            if item["status"] == "needs_user_confirmation"
        ]
        updated = [
            {
                "evidence_quote": item["evidence_quote"],
                "components": item["components"],
                "ownership_level": "contributed",
                "execution_mode": "supervised",
                "coverage": "partial",
                "scope_note": "完成已分配步骤",
            }
            for item in pending
        ]

        confirmed = self.post(
            client, sid,
            {
                "action": "confirm_activity_proposals",
                "activity_proposals": updated,
                "proposal_ids": [],
            },
        )

        self.assertEqual(confirmed["stage"], "representative_sample")
        canonical = confirmed["state"]["confirmed_canonical_experience"]
        self.assertEqual(len(canonical["evidence_ids"]), 2)

        before = confirmed["state"]["activity_proposals"]
        failed = self.post(
            client, sid,
            {
                "action": "confirm_activity_proposals",
                "activity_proposals": [
                    {**updated[0], "evidence_quote": "不存在的引文"}
                ],
                "proposal_ids": [],
            },
        )
        self.assertEqual(failed["state"]["activity_proposals"], before)


if __name__ == "__main__":
    unittest.main()
