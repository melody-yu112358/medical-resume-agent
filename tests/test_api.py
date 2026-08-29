import json
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from medical_career_agent.api import create_app
except ModuleNotFoundError:  # Core tests remain runnable before optional install.
    create_app = None


@unittest.skipIf(create_app is None, "Flask is not installed")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app(load_model_from_environment=False).test_client()

    def test_health_and_job_list(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        payload = health.get_json()
        self.assertFalse(payload["llm_configured"])
        self.assertEqual(payload["resume_agent_version"], "medical-resume-workflow-v1")
        self.assertEqual(payload["resume_agent_backend_persistence"], "local_session_json")
        jobs = self.client.get("/api/jobs").get_json()
        self.assertEqual(len(jobs), 1)
        self.assertTrue(jobs[0]["synthetic"])

    def test_root_redirects_to_launch_beta(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/demo/resume-agent/index.html")

    def test_text_resume_upload_returns_extracted_text(self):
        response = self.client.post(
            "/api/resume/upload",
            data={"file": (io.BytesIO("医学硕士，完成文献检索。".encode("utf-8")), "resume.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["resume_text"], "医学硕士，完成文献检索。")

    def test_match_endpoint(self):
        response = self.client.post(
            "/api/matches",
            json={
                "job_id": "synthetic-medical-affairs-sh-001",
                "resume_text": "医学硕士，负责PubMed文献检索和组会汇报。",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["report"]["scoring_version"], "deterministic-v1")
        self.assertIn("diagnose_resume", body["trace"])

    def test_custom_jd_endpoint(self):
        response = self.client.post(
            "/api/resume-beta/analyze",
            json={
                "title": "医学写作",
                "jd_text": "负责医学文献检索；撰写医学材料；跨团队沟通",
                "resume_text": "医学硕士，使用PubMed完成课题检索并进行组会汇报。",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["job"]["job_id"], "user-supplied-jd")
        self.assertIn("analyze_user_jd", body["trace"])

    def test_custom_jd_requires_both_inputs(self):
        response = self.client.post(
            "/api/resume-beta/analyze", json={"resume_text": "医学硕士"}
        )
        self.assertEqual(response.status_code, 400)

    def test_resume_intake_returns_verbatim_evidence_before_rewrite(self):
        response = self.client.post(
            "/api/resume-intake",
            json={
                "resume_text": "负责课题文献检索，使用PubMed筛选120篇文献。",
                "jd_text": "负责医学文献检索与解读；有GCP经验者优先",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["version"], "resume-intake-v0.1")
        self.assertEqual(
            body["evidence_matches"][0]["resume_quote"],
            "负责课题文献检索，使用PubMed筛选120篇文献",
        )
        self.assertEqual(body["evidence_matches"][1]["strength"], "none")

    def test_resume_structure_endpoint_returns_unconfirmed_section_candidates(self):
        response = self.client.post(
            "/api/resume-structures",
            json={
                "resume_text": (
                    "教育背景\n示例医学院 临床医学硕士\n"
                    "科研经历\n完成临床研究文献检索"
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["version"], "resume-structure-v0.1")
        self.assertEqual(
            [item["section_key"] for item in body["sections"]],
            ["education", "research_experience"],
        )
        self.assertEqual(body["evidence"][0]["status"], "extracted")

    def test_resume_review_flags_unconfirmed_number_before_export(self):
        response = self.client.post(
            "/api/resume-reviews",
            json={
                "resume_text": "负责课题文献检索，使用PubMed筛选120篇文献。",
                "jd_text": "负责医学文献检索；要求GCP经验",
                "final_resume_text": "主导文献检索，筛选500篇文献。",
            },
        )
        self.assertEqual(response.status_code, 200)
        codes = {item["code"] for item in response.get_json()["findings"]}
        self.assertIn("unconfirmed_number", codes)
        self.assertIn("responsibility_upgrade", codes)

    def test_resume_rewrite_falls_back_to_verbatim_evidence_without_model(self):
        response = self.client.post(
            "/api/resume-rewrites",
            json={
                "resume_text": "负责课题文献检索，使用PubMed筛选120篇文献。",
                "jd_text": "负责医学文献检索",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["mode"], "evidence_preserving_fallback")
        self.assertEqual(body["items"][0]["rewritten"], body["items"][0]["source_quote"])

    def test_profile_list_and_career_comparison_endpoint(self):
        profiles = self.client.get("/api/profiles")
        self.assertEqual(profiles.status_code, 200)
        self.assertEqual(len(profiles.get_json()), 3)

        response = self.client.post(
            "/api/career-comparisons",
            json={"profile_id": "synthetic-research-builder-002"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["scoring_version"], "career-comparison-v0.1")
        self.assertLessEqual(len(body["hypotheses"]), 3)
        self.assertEqual(
            body["hypotheses"][0]["career_id"],
            "healthcare-ai-product-manager",
        )
        self.assertIn("retrieve_career_cards", body["trace"])

    def test_profile_draft_endpoint_returns_unverified_grounded_evidence(self):
        source_text = (
            "我在研究生组会中检索并比较了十二篇临床研究，整理出结论、局限和"
            "待确认问题，随后完成了一次二十分钟汇报。"
        )

        class FakeDraftGateway:
            def generate(self, *, task, context):
                return json.dumps(
                    {
                        "evidence": [
                            {
                                "source_quote": "检索并比较了十二篇临床研究",
                                "capabilities": ["文献检索", "证据比较"],
                                "confidence": 0.8,
                            }
                        ],
                        "unknowns": ["尚不清楚是否保留了汇报材料"],
                        "follow_up_question": "你是否保留了汇报材料？",
                    },
                    ensure_ascii=False,
                )

        client = create_app(
            model_gateway=FakeDraftGateway(),
            load_model_from_environment=False,
        ).test_client()
        response = client.post(
            "/api/profile-drafts",
            json={
                "education_field": "临床医学",
                "education_stage": "硕士二年级",
                "experience_text": source_text,
                "constraints": {"locations": ["上海"]},
                "consent_confirmed": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        evidence = body["profile_draft"]["evidence"][0]
        self.assertEqual(evidence["confirmation_status"], "unverified")
        self.assertIn(evidence["source_quote"], source_text)
        self.assertFalse(body["privacy"]["persisted_by_backend"])

    def test_confirmed_temporary_profile_can_be_compared_without_storage(self):
        response = self.client.post(
            "/api/career-comparisons",
            json={
                "maximum_hypotheses": 3,
                "profile": {
                    "profile_confirmed": True,
                    "consent_recorded": True,
                    "education": {
                        "field": "临床医学",
                        "stage": "硕士二年级",
                    },
                    "evidence": [
                        {
                            "source_quote": "检索并比较了十二篇临床研究",
                            "capabilities": ["文献检索", "证据比较"],
                            "confidence": 0.8,
                            "confirmed": True,
                        }
                    ],
                    "constraints": {
                        "locations": ["上海"],
                        "weekly_learning_hours": 8,
                        "non_negotiables": [],
                    },
                    "unknowns": ["尚未验证英文写作"],
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["profile_id"], "session-confirmed-profile")
        self.assertIn("receive_confirmed_profile", body["trace"])
        self.assertTrue(body["hypotheses"])

    def test_invalid_comparison_and_demo_route(self):
        missing = self.client.post(
            "/api/career-comparisons",
            json={"profile_id": "missing-profile"},
        )
        self.assertEqual(missing.status_code, 400)
        self.assertIn("unknown profile_id", missing.get_json()["error"])

        demo = self.client.get("/demo/")
        try:
            self.assertEqual(demo.status_code, 200)
            self.assertIn("今天，你想走多深", demo.get_data(as_text=True))
        finally:
            demo.close()

        intake = self.client.get("/demo/profile-intake/index.html")
        try:
            self.assertEqual(intake.status_code, 200)
            self.assertIn("个人画像验证页", intake.get_data(as_text=True))
        finally:
            intake.close()

        glimpse = self.client.get("/demo/journey/glimpse.html")
        try:
            self.assertEqual(glimpse.status_code, 200)
            self.assertIn("可能性速览", glimpse.get_data(as_text=True))
        finally:
            glimpse.close()

        experiment = self.client.get("/demo/journey/experiment.html")
        try:
            self.assertEqual(experiment.status_code, 200)
            self.assertIn("七天验证工作台", experiment.get_data(as_text=True))
        finally:
            experiment.close()

        engineering_demo = self.client.get("/demo/integration.html")
        try:
            self.assertEqual(engineering_demo.status_code, 200)
            self.assertIn("职业比较", engineering_demo.get_data(as_text=True))
        finally:
            engineering_demo.close()

    def test_explanation_endpoint_requires_model_configuration(self):
        response = self.client.post(
            "/api/career-explanations",
            json={"profile_id": "synthetic-research-builder-002"},
        )
        self.assertEqual(response.status_code, 503)
        self.assertIn("LLM is not configured", response.get_json()["error"])

    def test_bounded_model_explanation_endpoint(self):
        class FakeModelGateway:
            def generate(self, *, task, context):
                lines = [
                    "以下内容只是对确定性比较结果的语言解释；证据覆盖率不是适合度。"
                ]
                for hypothesis in context["comparison"]["hypotheses"]:
                    evidence_id = hypothesis["supporting_evidence"][0]["evidence_id"]
                    lines.append(
                        f"### {hypothesis['career_name']}\n"
                        f"这是可修订的职业假设，引用画像证据 {evidence_id}。"
                        "仍需查看缺口、未知信息和现实约束，并完成给出的验证行动。"
                        "职业卡目前为 draft，需要人工复核。"
                    )
                return "\n\n".join(lines)

        client = create_app(
            model_gateway=FakeModelGateway(),
            load_model_from_environment=False,
        ).test_client()
        response = client.post(
            "/api/career-explanations",
            json={"profile_id": "synthetic-research-builder-002"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(
            body["explanation"]["model_role"],
            "language_explanation_only",
        )
        self.assertEqual(len(body["comparison"]["hypotheses"]), 3)
        self.assertTrue(body["explanation"]["cited_evidence_ids"])

    def test_confirmed_temporary_profile_can_receive_bounded_explanation(self):
        class FakeModelGateway:
            def generate(self, *, task, context):
                lines = ["以下只是语言解释；证据覆盖率不是适合度。"]
                for hypothesis in context["comparison"]["hypotheses"]:
                    evidence_id = hypothesis["supporting_evidence"][0]["evidence_id"]
                    lines.append(
                        f"### {hypothesis['career_name']}\n"
                        f"这是可修订假设，引用已确认的证据 {evidence_id}。"
                        "仍需检查缺口、未知信息和现实约束，并完成验证行动。"
                        "职业卡目前为 draft，需要人工复核。"
                    )
                return "\n\n".join(lines)

        client = create_app(
            model_gateway=FakeModelGateway(),
            load_model_from_environment=False,
        ).test_client()
        response = client.post(
            "/api/career-explanations",
            json={
                "profile": {
                    "profile_confirmed": True,
                    "consent_recorded": True,
                    "education": {
                        "field": "临床医学",
                        "stage": "硕士二年级",
                    },
                    "evidence": [
                        {
                            "source_quote": "检索并比较了十二篇临床研究",
                            "capabilities": ["文献检索", "证据比较"],
                            "confidence": 0.8,
                            "confirmed": True,
                        }
                    ],
                    "constraints": {
                        "locations": ["上海"],
                        "weekly_learning_hours": 8,
                        "non_negotiables": [],
                    },
                    "unknowns": ["尚未验证英文写作"],
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["comparison"]["profile_id"], "session-confirmed-profile")
        self.assertTrue(body["explanation"]["cited_evidence_ids"])

    def test_unsafe_model_output_is_rejected(self):
        class UnsafeModelGateway:
            def generate(self, *, task, context):
                return "这个结果说明你一定适合该职业。" * 20

        client = create_app(
            model_gateway=UnsafeModelGateway(),
            load_model_from_environment=False,
        ).test_client()
        response = client.post(
            "/api/career-explanations",
            json={"profile_id": "synthetic-research-builder-002"},
        )
        self.assertEqual(response.status_code, 502)
        self.assertIn("forbidden verdict language", response.get_json()["error"])

    def test_claim_gate_ready_for_valid_claim(self):
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "clinical_research_001",
            "evidence_ids": ["ev_001", "ev_002"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": "systematic review"},
            "role": {"title": "Research Assistant", "responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review", "meta_analysis"],
            "tools": ["endnote", "revman"],
            "objects": ["clinical_studies", "medical_literature"],
            "collaboration": ["research_team"],
            "artifacts": ["prisma_flowchart"],
            "outcomes": ["completed_systematic_review"],
            "scope": {"study_count": "50"},
            "unknowns": [],
            "status": "user_confirmed",
        }
        bullet_claim = {
            "schema_version": "bullet-claim-v1",
            "claim_id": "claim_001",
            "experience_id": "clinical_research_001",
            "role_pack": "doctoral_v1",
            "wording": "参与系统综述的文献检索与筛选工作，掌握循证研究方法。",
            "used_facts": ["actions:retrieve_literature", "actions:screen_studies", "methods:systematic_review"],
            "evidence_ids": ["ev_001", "ev_002"],
            "responsibility_level": "participated",
            "omitted_unknowns": [],
            "risk_flags": [],
            "verification_status": "candidate",
            "user_disposition": None,
        }
        response = self.client.post(
            "/api/claim-gate",
            json={"bullet_claim": bullet_claim, "canonical_experience": canonical_experience},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ready")

    def test_claim_gate_rejects_unconfirmed_fact(self):
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_api_001",
            "evidence_ids": ["ev_001"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
            "status": "user_confirmed",
        }
        bullet_claim = {
            "schema_version": "bullet-claim-v1",
            "claim_id": "claim_api_001",
            "experience_id": "exp_api_001",
            "role_pack": "doctoral_v1",
            "wording": "负责整个系统综述项目。",
            "used_facts": ["actions:fake_action"],
            "evidence_ids": ["ev_001"],
            "responsibility_level": "participated",
            "omitted_unknowns": [],
            "risk_flags": [],
            "verification_status": "candidate",
            "user_disposition": None,
        }
        response = self.client.post(
            "/api/claim-gate",
            json={"bullet_claim": bullet_claim, "canonical_experience": canonical_experience},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(any("used_facts_confirmed" in fc for fc in body["failed_checks"]))
        self.assertTrue(any("responsibility_not_upgraded" in fc for fc in body["failed_checks"]))

    def test_claim_gate_rejects_unknown_role_pack(self):
        bullet_claim = {
            "schema_version": "bullet-claim-v1",
            "claim_id": "claim_api_002",
            "experience_id": "exp_api_001",
            "role_pack": "nonexistent_role_pack",
            "wording": "参与文献检索。",
            "used_facts": [],
            "evidence_ids": ["ev_001"],
            "responsibility_level": "participated",
            "omitted_unknowns": [],
            "risk_flags": [],
            "verification_status": "candidate",
            "user_disposition": None,
        }
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_api_001",
            "evidence_ids": ["ev_001"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": [],
            "methods": [],
            "tools": [],
            "objects": [],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
            "status": "user_confirmed",
        }
        response = self.client.post(
            "/api/claim-gate",
            json={"bullet_claim": bullet_claim, "canonical_experience": canonical_experience},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "rejected")
        self.assertTrue(any("role_pack_load_error" in fc for fc in body["failed_checks"]))

    def test_claim_ledger_record_and_retrieve(self):
        bullet_claim = {
            "schema_version": "bullet-claim-v1",
            "claim_id": "ledger_claim_001",
            "experience_id": "exp_ledger_001",
            "role_pack": "doctoral_v1",
            "wording": "参与文献检索。",
            "used_facts": ["actions:retrieve_literature"],
            "evidence_ids": ["ev_001"],
            "responsibility_level": "participated",
            "omitted_unknowns": [],
            "risk_flags": [],
            "verification_status": "ready",
            "user_disposition": None,
        }
        response = self.client.post(
            "/api/claim-ledger/record",
            json={
                "session_id": "ledger_api_1",
                "bullet_claim": bullet_claim,
                "gate_status": "ready",
                "user_disposition": None,
            },
        )
        self.assertEqual(response.status_code, 200)
        record = response.get_json()
        self.assertEqual(record["claim_id"], "ledger_claim_001")
        self.assertTrue(record["is_valid"])

        # Retrieve the session claims
        session_response = self.client.get("/api/claim-ledger/session/ledger_api_1")
        self.assertEqual(session_response.status_code, 200)
        claims = session_response.get_json()
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["claim_id"], "ledger_claim_001")

    def test_claim_ledger_invalidate_claims(self):
        bullet_claim = {
            "schema_version": "bullet-claim-v1",
            "claim_id": "ledger_claim_002",
            "experience_id": "exp_ledger_001",
            "role_pack": "doctoral_v1",
            "wording": "参与文献检索。",
            "used_facts": ["actions:retrieve_literature"],
            "evidence_ids": ["ev_001"],
            "responsibility_level": "participated",
            "omitted_unknowns": [],
            "risk_flags": [],
            "verification_status": "ready",
            "user_disposition": None,
        }
        self.client.post(
            "/api/claim-ledger/record",
            json={
                "session_id": "ledger_api_2",
                "bullet_claim": bullet_claim,
                "gate_status": "ready",
                "user_disposition": None,
            },
        )
        response = self.client.post(
            "/api/claim-ledger/invalidate/claims",
            json={
                "session_id": "ledger_api_2",
                "claim_ids": ["ledger_claim_002"],
                "reason": "user_rejected",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn("ledger_claim_002", body["invalidated_claim_ids"])

        invalidated = self.client.get("/api/claim-ledger/invalidated/ledger_api_2").get_json()
        self.assertEqual(len(invalidated), 1)
        self.assertFalse(invalidated[0]["is_valid"])
        self.assertEqual(invalidated[0]["invalidated_reason"], "user_rejected")

    def test_claim_ledger_requires_session_id(self):
        response = self.client.post("/api/claim-ledger/record", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("session_id", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
