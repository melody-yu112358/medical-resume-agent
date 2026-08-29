import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.api import create_app


class ResumeConversationApiTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app(load_model_from_environment=False).test_client()
        created = self.client.post("/api/conversations", json={})
        self.assertEqual(created.status_code, 201)
        self.session_id = created.get_json()["session_id"]

    def message(self, payload):
        response = self.client.post(f"/api/conversations/{self.session_id}/messages", json=payload)
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def establish_confirmed_experience(self):
        source = "在导师指导下参与系统综述，使用 PubMed 检索文献并完成文献筛选。"
        self.message({"text": source, "consent_confirmed": True})
        state = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        facts = state["extracted_draft"]["extracted_facts"]
        proposal = {
            "evidence_quote": source,
            "components": {key: facts.get(key, []) for key in ("actions", "methods", "tools", "techniques", "objects", "artifacts")},
            "ownership_level": "contributed", "execution_mode": "supervised", "coverage": "full", "scope_note": None,
        }
        self.message({"action": "update_activity_proposals", "activity_proposals": [proposal]})
        proposal_id = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]["activity_proposals"][-1]["proposal_id"]
        return self.message({"action": "confirm_activity_proposals", "proposal_ids": [proposal_id]})

    def establish_claims(self):
        self.establish_confirmed_experience()
        return self.message({"action": "select_role_packs", "role_packs": ["doctoral_v1"]})

    def test_free_text_supplement_updates_confirmed_canonical_experience(self):
        self.establish_confirmed_experience()
        self.message({"action": "update_facts", "text": "我还使用 R 进行敏感性分析。", "consent_confirmed": True})
        result = self.message({"action": "confirm_facts"})
        canonical = result["resume_document"]["research_experience"][0]
        stored = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertIn("r", stored["confirmed_canonical_experience"]["tools"])
        self.assertIn("sensitivity_analysis", stored["confirmed_canonical_experience"]["methods"])
        self.assertEqual(canonical["evidence_ids"], stored["confirmed_canonical_experience"]["evidence_ids"])

    def test_explanation_question_does_not_enter_evidence(self):
        self.message({"text": "在导师指导下用 R 进行生信分析。", "consent_confirmed": True})
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        response = self.message({"text": "什么意思"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(after["evidence_records"], before["evidence_records"])
        self.assertEqual(after["extracted_draft"], before["extracted_draft"])
        self.assertIn("确认的目的", response["assistant_message"])

    def test_resume_generation_request_does_not_enter_evidence_before_confirmation(self):
        self.message({"text": "在导师指导下用 R 进行生信分析。", "consent_confirmed": True})
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        response = self.message({"text": "生成简历"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(after["evidence_records"], before["evidence_records"])
        self.assertEqual(after["extracted_draft"], before["extracted_draft"])
        self.assertIn("需要先确认事实", response["assistant_message"])

    def test_why_confirmation_does_not_change_canonical(self):
        self.establish_confirmed_experience()
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]["confirmed_canonical_experience"]
        self.message({"text": "为什么需要确认？"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]["confirmed_canonical_experience"]
        self.assertEqual(after, before)

    def test_unlabeled_new_fact_still_enters_supplement_flow(self):
        self.message({"text": "在导师指导下参与系统综述并完成文献筛选。", "consent_confirmed": True})
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        response = self.message({"text": "我还使用 R 进行敏感性分析。"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(len(after["evidence_records"]), len(before["evidence_records"]) + 1)
        self.assertIn("补充内容", response["assistant_message"])

    def test_no_model_unclear_free_text_does_not_pollute_evidence(self):
        self.message({"text": "在导师指导下参与系统综述并完成文献筛选。", "consent_confirmed": True})
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.message({"text": "我想再想想"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(after["evidence_records"], before["evidence_records"])
        self.assertEqual(after["extracted_draft"], before["extracted_draft"])

    def test_method_only_intake_does_not_claim_activity_cards_and_asks_for_actions(self):
        response = self.message({"text": "我在做meta分析", "consent_confirmed": True})
        state = response["state"]
        self.assertFalse(state["activity_proposals"])
        self.assertNotIn("待确认的活动卡", response["assistant_message"])
        self.assertIn("信息还不足以形成活动卡", response["assistant_message"])
        self.assertIn("具体负责了哪些步骤", response["assistant_message"])
        self.assertTrue(response["pending_question"])

    def test_ask_what_to_confirm_does_not_enter_evidence_and_describes_empty_activity_state(self):
        self.message({"text": "我在做meta分析", "consent_confirmed": True})
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        response = self.message({"text": "当前需要确认什么"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(after["evidence_records"], before["evidence_records"])
        self.assertIn("当前没有可确认的活动卡", response["assistant_message"])
        self.assertIn("具体负责了哪些步骤", response["assistant_message"])

    def test_ui_problem_report_does_not_enter_evidence(self):
        self.message({"text": "我在做meta分析", "consent_confirmed": True})
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        response = self.message({"text": "我看不到候选卡"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(after["evidence_records"], before["evidence_records"])
        self.assertIn("不是页面遗漏", response["assistant_message"])

    def test_natural_academic_target_selects_role_pack_without_evidence(self):
        self.establish_confirmed_experience()
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        response = self.message({"text": "保研"})
        after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(after["evidence_records"], before["evidence_records"])
        self.assertEqual(after["selected_role_packs"], ["doctoral_v1"])
        self.assertEqual(after["stage"], "factual_audit")
        self.assertIn("候选要点已生成", response["assistant_message"])

    def test_natural_target_and_wording_request_composes(self):
        self.establish_confirmed_experience()
        response = self.message({"text": "保研，给我措辞"})
        state = response["state"]
        self.assertEqual(state["selected_role_packs"], ["doctoral_v1"])
        self.assertEqual(state["stage"], "factual_audit")
        self.assertTrue(state["generated_claims"])

    def test_new_facts_return_to_confirmation_and_supersede_pending_proposals(self):
        self.establish_confirmed_experience()
        self.message({"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        old_claim_ids = [item["claim_id"] for item in before["generated_claims"]]
        response = self.message({"text": "我用 PubMed 检索文献，独立完成筛选，R 分析是在导师指导下做的。"})
        after = response["state"]
        self.assertEqual(after["stage"], "fact_confirmation")
        self.assertTrue(any(item["status"] == "superseded" for item in after["activity_proposals"]))
        self.assertTrue(any(item["status"] == "needs_user_confirmation" for item in after["activity_proposals"]))
        self.assertTrue(all(item["verification_status"] == "superseded" for item in after["generated_claims"] if item["claim_id"] in old_claim_ids))

    def test_natural_confirmation_with_unknown_scope_does_not_advance(self):
        self.message({"text": "我在导师指导下使用 R 进行数据分析。", "consent_confirmed": True})
        response = self.message({"text": "确认"})
        self.assertEqual(response["stage"], "fact_confirmation")
        self.assertIn("完成范围", response["assistant_message"])
        self.assertIn("整个既定流程", response["assistant_message"])

    def test_guidance_is_retained_and_chat_confirmation_only_asks_for_missing_fields(self):
        self.message({"text": "我在导师指导下用 R 完成meta分析，PubMed检索文献技能。", "consent_confirmed": True})
        state = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        pending = [item for item in state["activity_proposals"] if item["status"] == "needs_user_confirmation"]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["components"]["actions"], ["perform_analysis"])
        self.assertEqual(pending[0]["execution_mode"], "supervised")
        response = self.message({"text": "确认"})
        self.assertIn("对任务结果的承担", response["assistant_message"])
        self.assertIn("完成范围", response["assistant_message"])
        self.assertNotIn("执行方式、", response["assistant_message"])

    def test_chat_only_confirmation_can_confirm_a_complete_single_activity(self):
        self.message({"text": "我在导师指导下负责用 R 完成meta分析整个既定流程。", "consent_confirmed": True})
        response = self.message({"text": "确认"})
        self.assertEqual(response["stage"], "representative_sample")
        state = response["state"]
        self.assertTrue(state["confirmed_canonical_experience"])
        self.assertFalse(any(item["status"] == "needs_user_confirmation" for item in state["activity_proposals"]))

    def test_confirmed_proposal_is_not_pending_and_pending_reason_is_returned(self):
        self.establish_confirmed_experience()
        state = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertTrue(state["activity_proposals"])
        self.assertTrue(any(item["status"] == "confirmed" for item in state["activity_proposals"]))
        self.assertFalse(any(item["status"] == "needs_user_confirmation" for item in state["activity_proposals"]))
        self.message({"text": "我在导师指导下使用 R 进行数据分析。"})
        response = self.message({"text": "确认"})
        self.assertIn("待确认活动", response["assistant_message"])
        self.assertIn("show_activity_cards", response["ui_events"])

    def test_rewrite_request_explains_claim_gate_gap_when_no_ready_claim(self):
        self.establish_claims()
        state = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        claim = state["generated_claims"][0]
        self.message({"action": "edit_wording", "claim_id": claim["claim_id"], "wording": "主导 999 项临床研究并获得国际大奖。"})
        response = self.message({"text": "给我专业版措辞"})
        self.assertIn("目前没有可改写的 ready 要点", response["assistant_message"])
        self.assertNotIn("请选择目标方向", response["assistant_message"])

    def test_wording_edit_does_not_change_confirmed_facts(self):
        generated = self.establish_claims()
        state_before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        claim = state_before["generated_claims"][0]
        self.message({"action": "edit_wording", "claim_id": claim["claim_id"], "wording": "参与系统综述的文献检索与筛选工作。"})
        state_after = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        self.assertEqual(state_before["confirmed_canonical_experience"], state_after["confirmed_canonical_experience"])

    def test_fact_change_invalidates_old_claims_and_requires_new_gate(self):
        self.establish_claims()
        before = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        old_experience = before["confirmed_canonical_experience"]["experience_id"]
        self.message({"action": "update_facts", "text": "我负责了文献筛选工作。", "consent_confirmed": True})
        self.message({"action": "confirm_facts", "modified_facts": {"role.responsibility_level": "owned_component"}, "new_evidence": "我负责了预设标准下的文献筛选工作。"})
        ledger = self.client.get(f"/api/claim-ledger/invalidated/{self.session_id}").get_json()
        self.assertTrue(any(item["experience_id"] == old_experience for item in ledger))
        document = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]["resume_document"]
        self.assertFalse(document["research_experience"][0]["bullets"])
        state = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        pending = [item for item in state["activity_proposals"] if item["status"] == "needs_user_confirmation"]
        self.message({"action": "update_activity_proposals", "activity_proposals": [{"evidence_quote": "我负责了文献筛选工作。", "components": {"actions": ["screen_studies"], "methods": [], "tools": [], "techniques": [], "objects": ["medical_literature"], "artifacts": []}, "ownership_level": "owned_component", "execution_mode": "independent", "coverage": "full", "scope_note": None}]})
        proposal_id = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]["activity_proposals"][-1]["proposal_id"]
        self.message({"action": "confirm_activity_proposals", "proposal_ids": [proposal_id]})
        regenerated = self.message({"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        self.assertGreater(regenerated["audit_status"]["ready"], 0)

    def test_unready_claim_never_enters_resume_document(self):
        self.establish_claims()
        state = self.client.get(f"/api/conversations/{self.session_id}").get_json()["state"]
        claim = state["generated_claims"][0]
        response = self.message({"action": "edit_wording", "claim_id": claim["claim_id"], "wording": "主导 999 项临床研究并获得国际大奖。"})
        self.assertGreater(response["audit_status"]["not_ready"], 0)
        rendered = response["resume_document"]["research_experience"][0]["bullets"]
        self.assertFalse(any("999" in item["text"] for item in rendered))

    def test_reload_preserves_stage_facts_and_audit(self):
        self.establish_claims()
        response = self.client.get(f"/api/conversations/{self.session_id}")
        self.assertEqual(response.status_code, 200)
        state = response.get_json()["state"]
        self.assertEqual(state["stage"], "factual_audit")
        self.assertEqual(state["confirmed_canonical_experience"]["status"], "user_confirmed")
        self.assertTrue(state["claim_gate_results"])


if __name__ == "__main__":
    unittest.main()
