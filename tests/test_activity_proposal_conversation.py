import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from medical_career_agent.api import create_app


SOURCE = "师兄带我用 R 对研究数据做敏感性分析，后来我自己完成了一部分；文献筛选由我独立完成。"


class ActivityProposalConversationTest(unittest.TestCase):
    def client_with_model(self, proposals):
        class Gateway:
            def generate(self, *, task, context):
                if task == "resume_activity_proposals":
                    return json.dumps({"activity_proposals": proposals}, ensure_ascii=False)
                return json.dumps({"intent": None, "assistant_message": None})
        return create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()

    def create(self, client):
        return client.post("/api/conversations", json={}).get_json()["session_id"]

    def post(self, client, sid, body):
        response = client.post(f"/api/conversations/{sid}/messages", json=body)
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def proposals(self):
        return [
            {"evidence_quote": "师兄带我用 R 对研究数据做敏感性分析，后来我自己完成了一部分", "components": {"actions": ["perform_analysis"], "methods": ["sensitivity_analysis"], "tools": ["r"], "techniques": [], "objects": ["research_data"], "artifacts": []}, "ownership_level": "contributed", "execution_mode": "supervised", "coverage": "partial", "scope_note": "首次流程由师兄带领"},
            {"evidence_quote": "师兄带我用 R 对研究数据做敏感性分析，后来我自己完成了一部分", "components": {"actions": ["perform_analysis"], "methods": ["sensitivity_analysis"], "tools": ["r"], "techniques": [], "objects": ["research_data"], "artifacts": []}, "ownership_level": "owned_component", "execution_mode": "independent", "coverage": "partial", "scope_note": "后续部分步骤"},
            {"evidence_quote": "文献筛选由我独立完成", "components": {"actions": ["screen_studies"], "methods": [], "tools": [], "techniques": [], "objects": ["medical_literature"], "artifacts": []}, "ownership_level": "owned_component", "execution_mode": "independent", "coverage": "full", "scope_note": None},
        ]

    def test_llm_proposals_do_not_change_canonical_and_can_split_activity(self):
        client = self.client_with_model(self.proposals())
        sid = self.create(client)
        response = self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertIsNone(state["confirmed_canonical_experience"])
        self.assertEqual(len(state["activity_proposals"]), 3)
        self.assertEqual({item["execution_mode"] for item in state["activity_proposals"][:2]}, {"supervised", "independent"})

    def test_quote_not_in_source_is_rejected(self):
        bad = self.proposals(); bad[0]["evidence_quote"] = "模型编造的原文"
        client = self.client_with_model(bad); sid = self.create(client)
        self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertEqual(len(state["activity_proposals"]), 2)
        self.assertIsNone(state["confirmed_canonical_experience"])

    def test_intake_ignores_model_intent_and_records_hard_rejections(self):
        class Gateway:
            def generate(self, *, task, context):
                if task == "resume_conversation_intent":
                    return json.dumps({"intent": "edit_wording", "assistant_message": "错误路由"})
                if task == "resume_activity_proposals":
                    return json.dumps({"activity_proposals": [
                        {"evidence_quote": SOURCE, "components": {"actions": [], "methods": [], "tools": [], "techniques": [], "objects": [], "artifacts": []}, "ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown"},
                        {"evidence_quote": "不存在的引文", "components": {"actions": ["screen_studies"], "methods": [], "tools": [], "techniques": [], "objects": [], "artifacts": []}, "ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown"},
                    ]}, ensure_ascii=False)
                return json.dumps({})
        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = self.create(client)
        response = self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertEqual(response["stage"], "fact_confirmation")
        self.assertEqual(state["proposal_audits"][-1]["accepted_count"], 0)
        self.assertEqual(
            {item["reason"] for item in state["proposal_audits"][-1]["hard_rejections"]},
            {"atomic_activity_requires_action", "evidence_quote_must_be_nonempty_verbatim_source_substring_and_components_object"},
        )

    def test_unknown_responsibility_is_preserved_but_cannot_be_confirmed(self):
        unknown = self.proposals()[:1]
        unknown[0].update({"ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown"})
        client = self.client_with_model(unknown); sid = self.create(client)
        self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        proposal = state["activity_proposals"][0]
        self.assertEqual(proposal["execution_mode"], "unknown")
        response = self.post(client, sid, {"action": "confirm_activity_proposals", "proposal_ids": [proposal["proposal_id"]]})
        self.assertIn("缺少责任或范围确认", response["assistant_message"])

    def test_reject_does_not_change_canonical_then_confirm_writes_v2(self):
        client = self.client_with_model(self.proposals()); sid = self.create(client)
        self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        rejected = state["activity_proposals"][0]["proposal_id"]
        self.post(client, sid, {"action": "reject_activity_proposal", "proposal_id": rejected})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertIsNone(state["confirmed_canonical_experience"])
        pending = [item["proposal_id"] for item in state["activity_proposals"] if item["status"] == "needs_user_confirmation"]
        self.post(client, sid, {"action": "confirm_activity_proposals", "proposal_ids": pending})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertEqual(state["confirmed_canonical_experience"]["schema_version"], "canonical-experience-v2")
        self.assertEqual(len(state["confirmed_canonical_experience"]["activities"]), 2)
        composed = self.post(client, sid, {"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        persisted = client.get(f"/api/conversations/{sid}").get_json()["state"]
        reloaded = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertEqual(reloaded["claim_gate_results"], persisted["claim_gate_results"])
        self.assertEqual(composed["audit_status"]["ready"] + composed["audit_status"]["not_ready"], len(reloaded["claim_gate_results"]))

    def test_no_model_generates_manual_deterministic_proposals_and_reload_persists(self):
        client = create_app(load_model_from_environment=False).test_client(); sid = self.create(client)
        self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})
        reloaded = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertTrue(reloaded["activity_proposals"])
        self.assertTrue(all(item["execution_mode"] == "unknown" for item in reloaded["activity_proposals"]))
        pending = [item["proposal_id"] for item in reloaded["activity_proposals"]]
        response = self.post(client, sid, {"action": "confirm_activity_proposals", "proposal_ids": pending})
        self.assertIsNone(client.get(f"/api/conversations/{sid}").get_json()["state"]["confirmed_canonical_experience"])
        self.assertIn("缺少责任或范围确认", response["assistant_message"])


if __name__ == "__main__":
    unittest.main()
