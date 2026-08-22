import sys
import unittest
from pathlib import Path
from json import loads

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Import the services that will be implemented in later actions
# For now, we'll test the data structures and expected behavior


class EndToEndChainTest(unittest.TestCase):
    """Test the complete chain from user input to final bullet claims"""

    def setUp(self):
        self.example = loads((ROOT / "data" / "fixtures" / "meta-analysis-end-to-end-example.json").read_text(encoding="utf-8"))

    def test_complete_chain_structure(self):
        """验证完整链路的数据结构"""
        # 用户输入
        self.assertIsInstance(self.example["user_input"], str)

        # 证据记录
        self.assertIsInstance(self.example["evidence_records"], list)
        self.assertEqual(len(self.example["evidence_records"]), 1)

        # 提取的事实
        self.assertIsInstance(self.example["extracted_facts"], dict)
        self.assertIn("context", self.example["extracted_facts"])
        self.assertIn("role", self.example["extracted_facts"])
        self.assertIn("actions", self.example["extracted_facts"])
        self.assertIn("unknowns", self.example["extracted_facts"])

        # 引导问题
        self.assertIsInstance(self.example["clarifying_questions"], list)
        self.assertGreater(len(self.example["clarifying_questions"]), 0)

        # 标准经历
        self.assertIsInstance(self.example["canonical_experience"], dict)
        self.assertEqual(self.example["canonical_experience"]["schema_version"], "canonical-experience-v1")
        self.assertEqual(self.example["canonical_experience"]["status"], "user_confirmed")

        # Bullet Claims
        self.assertIsInstance(self.example["bullet_claims"], dict)
        expected_roles = ["doctoral_v1", "clinical_research_v1", "medical_affairs_v1", "health_ai_data_v1"]
        for role in expected_roles:
            self.assertIn(role, self.example["bullet_claims"])
            self.assertIsInstance(self.example["bullet_claims"][role], list)
            self.assertGreater(len(self.example["bullet_claims"][role]), 0)

    def test_fact_consistency_across_chain(self):
        """验证事实在整个链路中的一致性"""
        # 提取的事实应该与标准经历一致
        extracted = self.example["extracted_facts"]
        canonical = self.example["canonical_experience"]

        self.assertEqual(extracted["context"], canonical["context"])
        self.assertEqual(extracted["role"], canonical["role"])
        self.assertEqual(set(extracted["actions"]), set(canonical["actions"]))
        self.assertEqual(set(extracted["methods"]), set(canonical["methods"]))
        self.assertEqual(set(extracted["unknowns"]), set(canonical["unknowns"]))

    def test_bullet_claim_traceability(self):
        """验证Bullet Claim的可追溯性"""
        canonical = self.example["canonical_experience"]
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                # Claim应该引用正确的经历ID
                self.assertEqual(claim["experience_id"], canonical["experience_id"])

                # Claim使用的事实应该是标准经历中的子集
                for fact in claim["used_facts"]:
                    self.assertIn(fact, canonical["actions"] + canonical["methods"] + canonical["tools"] +
                                canonical["objects"] + canonical["artifacts"] + canonical["outcomes"])

                # 责任等级应该一致
                self.assertEqual(claim["responsibility_level"], canonical["role"]["responsibility_level"])

    def test_role_specific_value_expression(self):
        """验证岗位特定的价值表达"""
        # 每个岗位应该强调不同的价值角度
        doctoral_claim = self.example["bullet_claims"]["doctoral_v1"][0]["wording"]
        clinical_claim = self.example["bullet_claims"]["clinical_research_v1"][0]["wording"]
        affairs_claim = self.example["bullet_claims"]["medical_affairs_v1"][0]["wording"]
        health_claim = self.example["bullet_claims"]["health_ai_data_v1"][0]["wording"]

        # 考博：强调方法学和研究能力
        self.assertIn("循证研究方法", doctoral_claim)

        # 临床科研：强调执行和临床证据
        self.assertIn("临床研究证据", clinical_claim)

        # MSL：强调医学信息和证据转译
        self.assertIn("医学文献", affairs_claim)

        # 医疗数据：强调数据处理和分析
        self.assertIn("医疗研究数据", health_claim)

    def test_safety_boundaries(self):
        """验证安全边界"""
        all_wordings = " ".join([
            claim["wording"]
            for role_pack, claims in self.example["bullet_claims"].items()
            for claim in claims
        ])

        # 不应该包含禁止的内容
        forbidden_phrases = [
            "独立负责", "主导", "PRISMA", "XX篇", "数据库",
            "发表", "管理", "制定", "训练", "开发"
        ]

        for phrase in forbidden_phrases:
            if phrase in " ".join(self.example["forbidden_outputs"]):
                self.assertNotIn(phrase, all_wordings)


if __name__ == "__main__":
    unittest.main()