import sys
import unittest
from pathlib import Path
from json import loads

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jsonschema import validate


class DataAnalysisExampleTest(unittest.TestCase):

    def setUp(self):
        self.example = loads((ROOT / "data" / "fixtures" / "data-analysis-end-to-end-example.json").read_text(encoding="utf-8"))
        self.canonical_schema = loads((ROOT / "schemas" / "canonical-experience.schema.json").read_text(encoding="utf-8"))
        self.bullet_schema = loads((ROOT / "schemas" / "bullet-claim.schema.json").read_text(encoding="utf-8"))

    def test_user_input_matches_evidence(self):
        """用户原话应该与证据记录匹配"""
        self.assertEqual(self.example["user_input"], self.example["evidence_records"][0]["source_text"])

    def test_extracted_facts_are_consistent(self):
        """提取的事实应该与用户输入一致"""
        # 只能提取用户明确提到的内容
        self.assertIn("r_language", self.example["extracted_facts"]["tools"])
        self.assertIn("analyze_data", self.example["extracted_facts"]["actions"])
        self.assertIn("build_models", self.example["extracted_facts"]["actions"])

        # 不能推断未提及的内容
        self.assertNotIn("machine_learning", self.example["extracted_facts"]["methods"])
        self.assertNotIn("dataset_size", self.example["extracted_facts"]["scope"])

    def test_canonical_experience_validates(self):
        """标准经历记录应该通过Schema验证"""
        validate(instance=self.example["canonical_experience"], schema=self.canonical_schema)

    def test_bullet_claims_validate(self):
        """所有Bullet Claim都应该通过Schema验证"""
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                with self.subTest(role_pack=role_pack, claim_id=claim["claim_id"]):
                    validate(instance=claim, schema=self.bullet_schema)

    def test_four_roles_produce_different_expressions(self):
        """四个岗位应该产生明显不同的表达"""
        wordings = [claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        # 检查每个岗位的关键词
        self.assertTrue(any("回归模型构建" in w for w in wordings))  # doctoral
        self.assertTrue(any("科研结论验证" in w for w in wordings))  # clinical_research
        self.assertTrue(any("循证决策" in w for w in wordings))      # medical_affairs
        self.assertTrue(any("AI应用" in w for w in wordings))   # health_ai_data

        # 确保表达不同但事实相同
        self.assertEqual(len(set(wordings)), 4)

    def test_responsibility_level_consistent(self):
        """所有Claim的责任等级应该保持一致"""
        responsibility_levels = [claim["responsibility_level"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        self.assertTrue(all(level == "owned_component" for level in responsibility_levels))

    def test_no_forbidden_outputs(self):
        """不应该包含禁止的输出"""
        all_wordings = " ".join([claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims])
        for forbidden in self.example["forbidden_outputs"]:
            # 提取关键词进行检查
            if "独立开发" in forbidden:
                self.assertNotIn("独立开发", all_wordings)
            if "主导" in forbidden:
                self.assertNotIn("主导", all_wordings)

    def test_unknowns_are_omitted(self):
        """未知项不应该出现在最终表达中"""
        all_wordings = " ".join([claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims])
        unknowns = self.example["extracted_facts"]["unknowns"]
        # 检查数字相关的未知项没有被猜测
        self.assertNotIn("变量", all_wordings)  # variables_count

    def test_evidence_traceability(self):
        """每个Claim都应该能追溯到确认的证据"""
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                with self.subTest(role_pack=role_pack, claim_id=claim["claim_id"]):
                    self.assertEqual(claim["evidence_ids"], ["ev_003"])
                    self.assertEqual(claim["experience_id"], "exp_003")


if __name__ == "__main__":
    unittest.main()