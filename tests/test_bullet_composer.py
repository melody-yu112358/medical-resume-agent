import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.bullet_composer import BulletComposerService, BulletClaim


class BulletComposerServiceTest(unittest.TestCase):

    def setUp(self):
        self.service = BulletComposerService(role_packs_dir=ROOT / "data" / "role-packs")

    def test_compose_bullets_requires_valid_canonical_experience(self):
        """Should require valid canonical experience with correct schema version."""
        # Test missing schema version
        with self.assertRaises(ValueError):
            self.service.compose_bullets(
                canonical_experience={"experience_id": "test_1"},
                role_pack_name="doctoral_v1"
            )

        # Test wrong schema version
        with self.assertRaises(ValueError):
            self.service.compose_bullets(
                canonical_experience={"schema_version": "wrong-version", "experience_id": "test_1"},
                role_pack_name="doctoral_v1"
            )

        # Test non-confirmed status
        with self.assertRaises(ValueError):
            self.service.compose_bullets(
                canonical_experience={
                    "schema_version": "canonical-experience-v1",
                    "experience_id": "test_1",
                    "status": "rejected",
                    "evidence_ids": ["ev_1"]
                },
                role_pack_name="doctoral_v1"
            )

    def test_compose_bullets_requires_experience_id_and_evidence(self):
        """Should require experience_id and evidence_ids."""
        base_experience = {
            "schema_version": "canonical-experience-v1",
            "status": "user_confirmed"
        }

        # Test missing experience_id
        with self.assertRaises(ValueError):
            self.service.compose_bullets(
                canonical_experience={**base_experience, "evidence_ids": ["ev_1"]},
                role_pack_name="doctoral_v1"
            )

        # Test missing evidence_ids
        with self.assertRaises(ValueError):
            self.service.compose_bullets(
                canonical_experience={**base_experience, "experience_id": "test_1"},
                role_pack_name="doctoral_v1"
            )

        # Test empty evidence_ids
        with self.assertRaises(ValueError):
            self.service.compose_bullets(
                canonical_experience={**base_experience, "experience_id": "test_1", "evidence_ids": []},
                role_pack_name="doctoral_v1"
            )

    def test_compose_bullets_requires_valid_role_pack(self):
        """Should require valid role pack name."""
        valid_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "test_1",
            "status": "user_confirmed",
            "evidence_ids": ["ev_1"],
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "role": {"responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review", "meta_analysis"],
            "objects": ["clinical_studies", "medical_literature"]
        }

        # Test invalid role pack
        with self.assertRaises(ValueError):
            self.service.compose_bullets(
                canonical_experience=valid_experience,
                role_pack_name="invalid_role_pack"
            )

    def test_doctoral_v1_bullet_generation(self):
        """Should generate appropriate bullets for doctoral role pack."""
        experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "meta_analysis_1",
            "status": "user_confirmed",
            "evidence_ids": ["ev_001", "ev_002"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": "systematic review"},
            "role": {"responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review", "meta_analysis"],
            "objects": ["clinical_studies", "medical_literature"],
            "unknowns": ["database_count", "screening_criteria"]
        }

        bullets = self.service.compose_bullets(
            canonical_experience=experience,
            role_pack_name="doctoral_v1"
        )

        # Should generate 1-3 bullets
        self.assertGreater(len(bullets), 0)
        self.assertLessEqual(len(bullets), 3)

        # Check first bullet structure
        bullet = bullets[0]
        self.assertIsInstance(bullet, BulletClaim)
        self.assertTrue(bullet.claim_id.startswith("claim_"))
        self.assertEqual(bullet.experience_id, "meta_analysis_1")
        self.assertEqual(bullet.role_pack, "doctoral_v1")
        self.assertEqual(bullet.responsibility_level, "participated")
        self.assertEqual(bullet.evidence_ids, ("ev_001", "ev_002"))
        self.assertEqual(bullet.omitted_unknowns, ("database_count", "screening_criteria"))

        # Wording should contain expected elements
        self.assertIn("参与", bullet.wording)
        self.assertIn("文献", bullet.wording)
        self.assertNotIn("独立", bullet.wording)  # Should not escalate responsibility

    def test_clinical_research_v1_bullet_generation(self):
        """Should generate appropriate bullets for clinical research role pack."""
        experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "data_analysis_1",
            "status": "user_confirmed",
            "evidence_ids": ["ev_003", "ev_004"],
            "context": {"domain": "data_analysis", "setting": "research_project", "topic": "statistical analysis"},
            "role": {"responsibility_level": "owned_component"},
            "actions": ["analyze_data", "interpret_results"],
            "methods": ["statistical_analysis", "regression_modeling"],
            "objects": ["clinical_data", "research_outcomes"],
            "unknowns": ["sample_size", "p_value_threshold"]
        }

        bullets = self.service.compose_bullets(
            canonical_experience=experience,
            role_pack_name="clinical_research_v1"
        )

        self.assertGreater(len(bullets), 0)
        self.assertLessEqual(len(bullets), 3)

        bullet = bullets[0]
        self.assertEqual(bullet.responsibility_level, "owned_component")
        # Should not use restricted verbs like "负责", "主导", etc.
        self.assertNotIn("负责", bullet.wording)
        self.assertNotIn("主导", bullet.wording)
        self.assertNotIn("管理", bullet.wording)
        # Should contain some reasonable action words
        self.assertTrue(any(word in bullet.wording for word in ["完成", "执行", "支持", "贡献", "实施"]))

    def test_meta_analysis_uses_methods_tools_and_deliverables(self):
        experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "meta_analysis_2",
            "status": "user_confirmed",
            "evidence_ids": ["ev_001"],
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "role": {"responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies", "extract_data"],
            "methods": ["meta_analysis", "sensitivity_analysis"],
            "tools": ["pubmed", "embase", "r"],
            "techniques": [],
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": ["analysis_figures", "group_presentation"],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
        }

        wording = self.service.compose_bullets(
            canonical_experience=experience,
            role_pack_name="doctoral_v1",
        )[0].wording

        for expected in ("Meta", "敏感性分析", "PubMed", "Embase", "R", "结果图表", "组会汇报"):
            self.assertIn(expected, wording)
        self.assertNotIn("支持相关研究工作", wording)

    def test_meta_analysis_changes_emphasis_for_medical_roles(self):
        experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "meta_analysis_role_angles",
            "status": "user_confirmed",
            "evidence_ids": ["ev_001", "ev_002"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": "2 型糖尿病与心血管结局"},
            "role": {"responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies", "extract_data"],
            "methods": ["meta_analysis", "sensitivity_analysis"],
            "tools": ["pubmed", "embase", "r"],
            "techniques": [],
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": ["analysis_figures"],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
        }

        doctoral = self.service.compose_bullets(
            canonical_experience=experience, role_pack_name="doctoral_v1"
        )[0].wording
        medical_affairs = self.service.compose_bullets(
            canonical_experience=experience, role_pack_name="medical_affairs_v1"
        )[0].wording
        health_data = self.service.compose_bullets(
            canonical_experience=experience, role_pack_name="health_ai_data_v1"
        )[0].wording

        for wording in (doctoral, medical_affairs, health_data):
            self.assertIn("2 型糖尿病与心血管结局", wording)
            self.assertIn("参与", wording)
            self.assertNotIn("独立", wording)
        self.assertIn("医学证据整理", medical_affairs)
        self.assertIn("数据整理与分析", health_data)
        self.assertNotEqual(doctoral, medical_affairs)

    def test_fallback_bullet_creation(self):
        """Should create fallback bullet when patterns fail."""
        # Create experience with minimal facts that won't match patterns well
        experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "minimal_1",
            "status": "user_confirmed",
            "evidence_ids": ["ev_999"],
            "context": {"domain": "other", "setting": "other"},
            "role": {"responsibility_level": "participated"},
            "actions": ["unknown_action"],
            "methods": ["unknown_method"],
            "objects": ["unknown_object"],
            "unknowns": []
        }

        bullets = self.service.compose_bullets(
            canonical_experience=experience,
            role_pack_name="doctoral_v1"
        )

        self.assertEqual(len(bullets), 1)
        self.assertIn("fallback_construction", bullets[0].risk_flags)

    def test_bullet_claim_to_dict_format(self):
        """Generated bullets should have correct dict format matching schema."""
        experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "test_1",
            "status": "user_confirmed",
            "evidence_ids": ["ev_1"],
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "role": {"responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "objects": ["medical_literature"],
            "unknowns": []
        }

        bullets = self.service.compose_bullets(
            canonical_experience=experience,
            role_pack_name="doctoral_v1"
        )

        bullet_dict = bullets[0].to_dict()

        # Check required fields per bullet-claim.schema.json
        self.assertEqual(bullet_dict["schema_version"], "bullet-claim-v1")
        self.assertTrue(bullet_dict["claim_id"].startswith("claim_"))
        self.assertEqual(bullet_dict["experience_id"], "test_1")
        self.assertEqual(bullet_dict["role_pack"], "doctoral_v1")
        self.assertIsInstance(bullet_dict["wording"], str)
        self.assertIsInstance(bullet_dict["used_facts"], list)
        self.assertEqual(bullet_dict["evidence_ids"], ["ev_1"])
        self.assertEqual(bullet_dict["responsibility_level"], "participated")
        self.assertIsInstance(bullet_dict["omitted_unknowns"], list)
        self.assertIsInstance(bullet_dict["risk_flags"], list)
        self.assertEqual(bullet_dict["verification_status"], "candidate")
        self.assertIsNone(bullet_dict["user_disposition"])

    def test_responsibility_level_preservation(self):
        """Should preserve original responsibility level without escalation."""
        test_cases = [
            ("participated", ["参与", "协助"]),
            ("owned_component", ["负责", "完成"]),
            ("led_delivery", ["主导"]),  # Note: clinical_research restricts this
            ("project_owner", ["负责"]),
        ]

        experience_base = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "test_1",
            "status": "user_confirmed",
            "evidence_ids": ["ev_1"],
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "objects": ["medical_literature"],
            "unknowns": []
        }

        for level, expected_verbs in test_cases:
            with self.subTest(level=level):
                experience = {**experience_base, "role": {"responsibility_level": level}}

                # Use doctoral_v1 which allows more verbs
                bullets = self.service.compose_bullets(
                    canonical_experience=experience,
                    role_pack_name="doctoral_v1"
                )

                if bullets:
                    wording = bullets[0].wording
                    # Should contain at least one expected verb
                    self.assertTrue(
                        any(verb in wording for verb in expected_verbs),
                        f"Expected one of {expected_verbs} in '{wording}' for level {level}"
                    )

    def test_forbidden_claims_avoidance(self):
        """Should avoid generating forbidden claims."""
        # Test with experience that might trigger forbidden patterns
        experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "test_forbidden",
            "status": "user_confirmed",
            "evidence_ids": ["ev_1"],
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "role": {"responsibility_level": "participated"},  # Low level
            "actions": ["design"],
            "methods": ["clinical_trial_design"],
            "objects": ["study_protocol"],
            "unknowns": []
        }

        # clinical_research_v1 has forbidden claims like "负责临床试验运营"
        bullets = self.service.compose_bullets(
            canonical_experience=experience,
            role_pack_name="clinical_research_v1"
        )

        for bullet in bullets:
            # Should not contain forbidden patterns
            self.assertNotIn("负责临床试验运营", bullet.wording)
            self.assertNotIn("确保合规", bullet.wording)
            # Should not escalate to "负责" since responsibility_level is "participated"
            self.assertNotIn("负责", bullet.wording)


if __name__ == "__main__":
    unittest.main()
