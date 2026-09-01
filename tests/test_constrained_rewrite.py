import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from medical_career_agent.api import create_app


SOURCE = "我独立完成系统综述的文献筛选。"
PROPOSAL = {"evidence_quote": SOURCE, "components": {"actions": ["screen_studies"], "methods": ["systematic_review"], "tools": [], "techniques": [], "objects": ["medical_literature"], "artifacts": []}, "ownership_level": "owned_component", "execution_mode": "independent", "coverage": "full", "scope_note": None}


class ConstrainedRewriteTest(unittest.TestCase):
    def setUp(self):
        class Gateway:
            def generate(_, *, task, context):
                if task == "resume_constrained_rewrite":
                    source = context["source_claim"]
                    wording = "独立完成系统综述的文献筛选。"
                    if "更强" in context["user_instruction"]:
                        wording = "主导系统综述并独立完成全部文献筛选。"
                    return json.dumps({"wording": wording, "used_facts": source["used_facts"], "dependency_refs": source["dependency_refs"], "evidence_ids": source["evidence_ids"]}, ensure_ascii=False)
                raise AssertionError(f"unexpected model task: {task}")
        self.client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        self.sid = self.client.post("/api/conversations", json={}).get_json()["session_id"]
        self.post({"text": SOURCE, "consent_confirmed": True})
        self.post({
            "action": "confirm_activity_proposals",
            "activity_proposals": [PROPOSAL],
            "proposal_ids": [],
        })
        self.post({"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        self.source_claim = self.state()["generated_claims"][0]

    def post(self, body):
        result = self.client.post(f"/api/conversations/{self.sid}/messages", json=body)
        self.assertEqual(result.status_code, 200, result.get_json())
        return result.get_json()

    def state(self):
        return self.client.get(f"/api/conversations/{self.sid}").get_json()["state"]

    def test_all_tones_keep_same_confirmed_facts_and_create_new_versions(self):
        ids = []
        for tone in ("Conservative", "Professional", "High-impact"):
            response = self.post({"action": "rewrite_claim", "source_claim_id": self.source_claim["claim_id"], "tone": tone, "instruction": "专业一点"})
            candidate = self.state()["generated_claims"][-1]
            ids.append(candidate["claim_id"])
            self.assertEqual(candidate["used_facts"], self.source_claim["used_facts"])
            self.assertEqual(candidate["dependency_refs"], self.source_claim["dependency_refs"])
            self.assertEqual(candidate["evidence_ids"], self.source_claim["evidence_ids"])
            self.assertEqual(candidate["verification_status"], "ready")
            rendered = response["resume_document"]["research_experience"][0]["bullets"]
            self.assertFalse(any(item["text"] == candidate["wording"] for item in rendered))
            self.assertTrue(any(item["text"] == self.source_claim["wording"] for item in rendered))
        self.assertEqual(len(set(ids)), 3)
        self.assertIn(self.source_claim["claim_id"], [item["claim_id"] for item in self.state()["generated_claims"]])

    def test_stronger_instruction_cannot_upgrade_responsibility_or_enter_resume(self):
        response = self.post({"action": "rewrite_claim", "source_claim_id": self.source_claim["claim_id"], "tone": "High-impact", "instruction": "更强一点"})
        candidate = self.state()["generated_claims"][-1]
        self.assertNotEqual(candidate["verification_status"], "ready")
        self.assertGreater(response["audit_status"]["not_ready"], 0)
        bullets = response["resume_document"]["research_experience"][0]["bullets"]
        self.assertFalse(any("主导" in item["text"] for item in bullets))

    def test_candidate_choice_and_audit_persist_after_reload(self):
        self.post({"action": "rewrite_claim", "source_claim_id": self.source_claim["claim_id"], "tone": "Professional", "instruction": "专业一点"})
        candidate = self.state()["generated_claims"][-1]
        self.post({"action": "select_rewrite_candidate", "claim_id": candidate["claim_id"]})
        reloaded = self.state()
        self.assertTrue(next(item for item in reloaded["rewrite_candidates"] if item["claim_id"] == candidate["claim_id"])["selected"])
        self.assertIn(candidate["claim_id"], reloaded["claim_gate_results"])
        document = reloaded["resume_document"]
        rendered = document["research_experience"][0]["bullets"]
        self.assertTrue(any(item["text"] == candidate["wording"] for item in rendered))
        self.assertFalse(any(item["text"] == self.source_claim["wording"] for item in rendered))

    def test_no_model_keeps_deterministic_base_flow_available(self):
        client = create_app(load_model_from_environment=False).test_client()
        sid = client.post("/api/conversations", json={}).get_json()["session_id"]
        response = client.post(f"/api/conversations/{sid}/messages", json={"text": "参与系统综述并完成文献筛选。", "consent_confirmed": True})
        self.assertEqual(response.status_code, 200)
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        self.assertEqual(state["stage"], "fact_confirmation")
        self.assertTrue(state["activity_proposals"])

    def test_supervised_partial_rewrite_cannot_become_independent_full(self):
        source = "导师指导我用 R 对研究数据做敏感性分析的一部分。"
        proposal = {"evidence_quote": source, "components": {"actions": ["perform_analysis"], "methods": ["sensitivity_analysis"], "tools": ["r"], "techniques": [], "objects": ["research_data"], "artifacts": []}, "ownership_level": "contributed", "execution_mode": "supervised", "coverage": "partial", "scope_note": None}
        class Gateway:
            def generate(_, *, task, context):
                if task == "resume_constrained_rewrite":
                    claim = context["source_claim"]
                    return json.dumps({"wording": "独立完成 R 敏感性分析完整流程。", "used_facts": claim["used_facts"], "dependency_refs": claim["dependency_refs"], "evidence_ids": claim["evidence_ids"]}, ensure_ascii=False)
                raise AssertionError(f"unexpected model task: {task}")
        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = client.post("/api/conversations", json={}).get_json()["session_id"]
        client.post(f"/api/conversations/{sid}/messages", json={"text": source, "consent_confirmed": True})
        client.post(f"/api/conversations/{sid}/messages", json={"action": "confirm_activity_proposals", "activity_proposals": [proposal], "proposal_ids": []})
        client.post(f"/api/conversations/{sid}/messages", json={"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        source_claim = client.get(f"/api/conversations/{sid}").get_json()["state"]["generated_claims"][0]
        response = client.post(f"/api/conversations/{sid}/messages", json={"action": "rewrite_claim", "source_claim_id": source_claim["claim_id"], "tone": "High-impact", "instruction": "更强"})
        candidate = client.get(f"/api/conversations/{sid}").get_json()["state"]["generated_claims"][-1]
        self.assertNotEqual(candidate["verification_status"], "ready")
        self.assertFalse(any("独立完成" in item["text"] for item in response.get_json()["resume_document"]["research_experience"][0]["bullets"]))

    def test_rewrite_cannot_switch_source_dependencies(self):
        second = "导师指导我用 R 对研究数据做敏感性分析的一部分。"
        first = "我独立完成系统综述的文献筛选。"
        proposals = [
            {"evidence_quote": first, "components": {"actions": ["screen_studies"], "methods": ["systematic_review"], "tools": [], "techniques": [], "objects": ["medical_literature"], "artifacts": []}, "ownership_level": "owned_component", "execution_mode": "independent", "coverage": "full", "scope_note": None},
            {"evidence_quote": second, "components": {"actions": ["perform_analysis"], "methods": ["sensitivity_analysis"], "tools": ["r"], "techniques": [], "objects": ["research_data"], "artifacts": []}, "ownership_level": "contributed", "execution_mode": "supervised", "coverage": "partial", "scope_note": None},
        ]
        class Gateway:
            def generate(_, *, task, context):
                if task == "resume_constrained_rewrite":
                    return json.dumps({"wording": "在指导下参与 R 敏感性分析的一部分。", "used_facts": ["actions:perform_analysis"], "dependency_refs": {"activity_ids": [context["canonical_experience"]["activities"][1]["activity_id"]], "responsibility_ids": [context["canonical_experience"]["task_responsibilities"][1]["responsibility_id"]], "completeness": "complete"}, "evidence_ids": context["source_claim"]["evidence_ids"]}, ensure_ascii=False)
                raise AssertionError(f"unexpected model task: {task}")
        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = client.post("/api/conversations", json={}).get_json()["session_id"]
        client.post(f"/api/conversations/{sid}/messages", json={"text": first + second, "consent_confirmed": True})
        client.post(f"/api/conversations/{sid}/messages", json={"action": "confirm_activity_proposals", "activity_proposals": proposals, "proposal_ids": []})
        client.post(f"/api/conversations/{sid}/messages", json={"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        source = client.get(f"/api/conversations/{sid}").get_json()["state"]["generated_claims"][0]
        response = client.post(f"/api/conversations/{sid}/messages", json={"action": "rewrite_claim", "source_claim_id": source["claim_id"], "tone": "Professional", "instruction": "专业一点"})
        state = client.get(f"/api/conversations/{sid}").get_json()["state"]
        candidate = state["generated_claims"][-1]
        self.assertNotEqual(candidate["verification_status"], "ready")
        self.assertTrue(any("rewrite_source_traceability" in item for item in state["claim_gate_results"][candidate["claim_id"]]["failed_checks"]))
        self.assertFalse(any(item["text"] == candidate["wording"] for item in response.get_json()["resume_document"]["research_experience"][0]["bullets"]))

    def test_tiers_can_use_distinct_safe_wording_with_identical_traceability(self):
        tier_wording = {
            "Conservative": "独立完成系统综述的文献筛选。",
            "Professional": "独立完成系统综述文献筛选流程。",
            "High-impact": "围绕系统综述流程，独立推进文献筛选工作。",
        }
        class Gateway:
            def generate(_, *, task, context):
                if task == "resume_constrained_rewrite":
                    source = context["source_claim"]
                    return json.dumps({"wording": tier_wording[context["tone"]], "used_facts": source["used_facts"], "dependency_refs": source["dependency_refs"], "evidence_ids": source["evidence_ids"]}, ensure_ascii=False)
                raise AssertionError(f"unexpected model task: {task}")
        client = create_app(model_gateway=Gateway(), load_model_from_environment=False).test_client()
        sid = client.post("/api/conversations", json={}).get_json()["session_id"]
        client.post(f"/api/conversations/{sid}/messages", json={"text": SOURCE, "consent_confirmed": True})
        client.post(f"/api/conversations/{sid}/messages", json={"action": "confirm_activity_proposals", "activity_proposals": [PROPOSAL], "proposal_ids": []})
        client.post(f"/api/conversations/{sid}/messages", json={"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        source = client.get(f"/api/conversations/{sid}").get_json()["state"]["generated_claims"][0]
        candidates = []
        for tone in tier_wording:
            client.post(f"/api/conversations/{sid}/messages", json={"action": "rewrite_claim", "source_claim_id": source["claim_id"], "tone": tone, "instruction": "专业一点"})
            candidates.append(client.get(f"/api/conversations/{sid}").get_json()["state"]["generated_claims"][-1])
        self.assertEqual({item["wording"] for item in candidates}, set(tier_wording.values()))
        for candidate in candidates:
            self.assertEqual(candidate["used_facts"], source["used_facts"])
            self.assertEqual(candidate["dependency_refs"], source["dependency_refs"])
            self.assertEqual(candidate["evidence_ids"], source["evidence_ids"])
            self.assertEqual(candidate["verification_status"], "ready")


if __name__ == "__main__":
    unittest.main()
