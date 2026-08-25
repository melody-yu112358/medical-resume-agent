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
        self.message({"text": "在导师指导下参与系统综述，使用 PubMed 检索文献并完成文献筛选。", "consent_confirmed": True})
        return self.message({"action": "confirm_facts"})

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
