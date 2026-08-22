import sys
import unittest
from pathlib import Path
from json import loads

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jsonschema import validate


class WetLabExampleTest(unittest.TestCase):

    def setUp(self):
        self.example = loads((ROOT / "data" / "fixtures" / "wet-lab-end-to-end-example.json").read_text(encoding="utf-8"))
        self.canonical_schema = loads((ROOT / "schemas" / "canonical-experience.schema.json").read_text(encoding="utf-8"))
        self.bullet_schema = loads((ROOT / "schemas" / "bullet-claim.schema.json").read_text(encoding="utf-8"))

    def test_user_input_matches_evidence(self):
        """用户原话应该与证据记录匹配"""
        self.assertEqual(self.example["user_input"], self.example["evidence_records"][0]["source_text"])

    def test_extracted_facts_are_consistent(self):
        """提取的事实应该与用户输入一致"""
        # 只能提取用户明确提到的内容
        self.assertIn("cell_culture", self.example["extracted_facts"]["methods"])
        self.assertIn("western_blot", self.example["extracted_facts"]["methods"])
        self.assertIn("culture_cells", self.example["extracted_facts"]["actions"])

        # 不能推断未提及的内容
        self.assertNotIn("crispr", self.example["extracted_facts"]["methods"])
        self.assertNotIn("cell_type", self.example["extracted_facts"]["scope"])

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
        self.assertTrue(any("分子生物学实验技术" in w for w in wordings))  # doctoral
        self.assertTrue(any("临床前研究工作" in w for w in wordings))  # clinical_research
        self.assertTrue(any("实验数据生成过程" in w for w in wordings))      # medical_affairs
        self.assertTrue(any("生物医学数据分析" in w for w in wordings))   # health_ai_data

        # 确保表达不同但事实相同
        self.assertEqual(len(set(wordings)), 4)

    def test_responsibility_level_consistent(self):
        """所有Claim的责任等级应该保持一致"""
        responsibility_levels = [claim["responsibility_level"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        self.assertTrue(all(level == "participated" for level in responsibility_levels))

    def test_no_forbidden_outputs(self):
        """不应该包含禁止的输出"""
        all_wordings = " ".join([claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims])
        for forbidden in self.example["forbidden_outputs"]:
            # 提取关键词进行检查
            if "独立负责" in forbidden:
                self.assertNotIn("独立负责", all_wordings)
            if "主导" in forbidden:
                self.assertNotIn("主导", all_wordings)

    def test_unknowns_are_omitted(self):
        """未知项不应该出现在最终表达中"""
        all_wordings = " ".join([claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims])
        unknowns = self.example["extracted_facts"]["unknowns"]
        # 检查数字相关的未知项没有被猜测
        self.assertNotIn("次", all_wordings)  # experiment_count

    def test_evidence_traceability(self):
        """每个Claim都应该能追溯到确认的证据"""
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                with self.subTest(role_pack=role_pack, claim_id=claim["claim_id"]):
                    self.assertEqual(claim["evidence_ids"], ["ev_004"])
                    self.assertEqual(claim["experience_id"], "exp_004")


if __name__ == "__main__":
    unittest.main()