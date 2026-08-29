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
        unknown[0]["evidence_quote"] = "R 对研究数据做敏感性分析"
        unknown[0].update({"ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown"})
        client = self.client_with_model(unknown); sid = self.create(client)
        self.post(client, sid, {"text": SOURCE, "consent_confirmed": True})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        proposal = state["activity_proposals"][0]
        self.assertEqual(proposal["execution_mode"], "unknown")
        response = self.post(client, sid, {"action": "confirm_activity_proposals", "proposal_ids": [proposal["proposal_id"]]})
        self.assertIn("缺少责任或范围确认", response["assistant_message"])

    def test_explicit_responsibility_enriches_a_conservative_model_proposal(self):
        source = "我在导师指导下负责用 R 完成 meta 分析整个既定流程。"

        class Gateway:
            def generate(self, *, task, context):
                if task == "resume_conversation_turn_plan":
                    # The model may be conversationally useful but omit an action.
                    return json.dumps({"assistant_message": "我理解了。", "proposed_actions": []}, ensure_ascii=False)
                if task == "resume_activity_proposals":
                    return json.dumps({"activity_proposals": [{
                        "evidence_quote": source,
                        "components": {"actions": ["perform_analysis"], "methods": ["meta_analysis"], "tools": ["r"], "techniques": [], "objects": [], "artifacts": []},
                        "ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown", "scope_note": None,
                    }]}, ensure_ascii=False)
                return json.dumps({"assistant_message": "收到。", "proposed_actions": []}, ensure_ascii=False)

        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = self.create(client)
        initial = self.post(client, sid, {"text": source, "consent_confirmed": True})
        proposal = initial["state"]["activity_proposals"][0]
        self.assertEqual((proposal["ownership_level"], proposal["execution_mode"], proposal["scope"]["coverage"]), ("owned_component", "supervised", "full"))
        confirmed = self.post(client, sid, {"text": "确认"})
        self.assertEqual(confirmed["stage"], "representative_sample")

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
        self.assertTrue(any(item["execution_mode"] in {"unknown", "supervised", "independent"} for item in reloaded["activity_proposals"]))
        pending = [item["proposal_id"] for item in reloaded["activity_proposals"]]
        response = self.post(client, sid, {"action": "confirm_activity_proposals", "proposal_ids": pending})
        self.assertIsNone(client.get(f"/api/conversations/{sid}").get_json()["state"]["confirmed_canonical_experience"])
        self.assertIn("缺少责任或范围确认", response["assistant_message"])

    def test_turn_plan_failure_falls_back_without_a_500(self):
        class Gateway:
            def generate(self, *, task, context):
                if task == "resume_conversation_turn_plan":
                    raise RuntimeError("temporarily unavailable")
                if task == "resume_activity_proposals":
                    return json.dumps({"activity_proposals": []})
                return json.dumps({})

        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = self.create(client)
        response = self.post(client, sid, {"text": "我在做meta分析", "consent_confirmed": True})
        self.assertEqual(response["stage"], "fact_confirmation")
        self.assertEqual(response["state"]["language_audit"][-1]["turn_plan_error"], "RuntimeError")

    def test_turn_plan_can_propose_facts_without_writing_canonical(self):
        source = "我使用 PubMed 检索文献并完成文献筛选。"

        class Gateway:
            def generate(self, *, task, context):
                if task == "resume_conversation_turn_plan":
                    return json.dumps({"assistant_message": "我目前理解你完成了文献检索与筛选，接下来核对责任边界。", "proposed_actions": [{"type": "propose_fact_update", "evidence_quote": source}], "needs_user_reply": True}, ensure_ascii=False)
                if task == "resume_activity_proposals":
                    return json.dumps({"activity_proposals": []})
                return json.dumps({})

        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = self.create(client)
        response = self.post(client, sid, {"text": source, "consent_confirmed": True})
        self.assertIn("我目前理解", response["assistant_message"])
        self.assertEqual(response["stage"], "fact_confirmation")
        self.assertIsNone(response["state"]["confirmed_canonical_experience"])
        self.assertEqual(response["state"]["language_audit"][-1]["turn_plan_actions"], ["propose_fact_update"])

    def test_turn_plan_fact_action_still_requires_consent(self):
        source = "我使用 PubMed 检索文献。"

        class Gateway:
            def generate(self, *, task, context):
                if task == "resume_conversation_turn_plan":
                    return json.dumps({"assistant_message": "我可以记录这条经历。", "proposed_actions": [{"type": "propose_fact_update", "evidence_quote": source}], "needs_user_reply": False}, ensure_ascii=False)
                return json.dumps({"activity_proposals": []})

        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = self.create(client)
        response = self.post(client, sid, {"text": source})
        self.assertIn("确认这段经历真实准确", response["assistant_message"])
        self.assertFalse(response["state"]["evidence_records"])

    def test_activity_proposal_model_failure_falls_back_without_a_500(self):
        source = "我使用 PubMed 检索文献。"

        class Gateway:
            def generate(self, *, task, context):
                if task == "resume_conversation_turn_plan":
                    return json.dumps({"proposed_actions": [{"type": "propose_fact_update", "evidence_quote": source}]}, ensure_ascii=False)
                if task == "resume_activity_proposals":
                    raise RuntimeError("temporarily unavailable")
                return json.dumps({})

        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = self.create(client)
        response = self.post(client, sid, {"text": source, "consent_confirmed": True})
        self.assertEqual(response["stage"], "fact_confirmation")
        self.assertEqual(response["state"]["language_audit"][-1]["activity_proposal_error"], "RuntimeError")

    def test_deterministic_activities_keep_retrieval_screening_and_r_analysis_separate(self):
        client = create_app(load_model_from_environment=False).test_client()
        sid = self.create(client)
        self.post(client, sid, {"text": "用 PubMed 检索文献，完成文献筛选，并用 R 做敏感性分析。", "consent_confirmed": True})
        proposals = client.get(f"/api/conversations/{sid}").get_json()["state"]["activity_proposals"]
        by_action = {item["components"]["actions"][0]: item["components"] for item in proposals}
        self.assertEqual(by_action["retrieve_literature"]["tools"], ["pubmed"])
        self.assertFalse(by_action["screen_studies"]["tools"])
        self.assertEqual(by_action["perform_analysis"]["tools"], ["r"])
        self.assertEqual(by_action["perform_analysis"]["methods"], ["sensitivity_analysis"])


if __name__ == "__main__":
    unittest.main()
