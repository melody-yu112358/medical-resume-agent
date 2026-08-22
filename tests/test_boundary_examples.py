import sys
import unittest
from pathlib import Path
from json import loads

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jsonschema import validate


class InformationInsufficientExampleTest(unittest.TestCase):
    """信息不足样例：系统不得编造具体任务、方法或结果。"""

    def setUp(self):
        self.example = loads((ROOT / "data" / "fixtures" / "information-insufficient-end-to-end-example.json").read_text(encoding="utf-8"))
        self.canonical_schema = loads((ROOT / "schemas" / "canonical-experience.schema.json").read_text(encoding="utf-8"))
        self.bullet_schema = loads((ROOT / "schemas" / "bullet-claim.schema.json").read_text(encoding="utf-8"))

    def test_user_input_matches_evidence(self):
        self.assertEqual(self.example["user_input"], self.example["evidence_records"][0]["source_text"])

    def test_no_fabricated_facts(self):
        # 信息不足时不能提取具体行动、方法、工具或产出
        self.assertEqual(self.example["extracted_facts"]["actions"], [])
        self.assertEqual(self.example["extracted_facts"]["methods"], [])
        self.assertEqual(self.example["extracted_facts"]["tools"], [])
        self.assertEqual(self.example["extracted_facts"]["artifacts"], [])
        self.assertEqual(self.example["extracted_facts"]["scope"], {})

    def test_unknowns_are_listed(self):
        self.assertGreater(len(self.example["extracted_facts"]["unknowns"]), 0)

    def test_clarifying_questions_present(self):
        self.assertGreater(len(self.example["clarifying_questions"]), 0)

    def test_canonical_experience_validates(self):
        validate(instance=self.example["canonical_experience"], schema=self.canonical_schema)

    def test_bullet_claims_validate(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                with self.subTest(role_pack=role_pack, claim_id=claim["claim_id"]):
                    validate(instance=claim, schema=self.bullet_schema)

    def test_insufficient_detail_flagged(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                self.assertIn("insufficient_detail", claim["risk_flags"])
                self.assertEqual(claim["verification_status"], "needs_confirmation")

    def test_no_specific_claims_when_detail_missing(self):
        all_wordings = " ".join(
            [claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        )
        self.assertNotIn("负责", all_wordings)
        self.assertNotIn("掌握", all_wordings)
        self.assertNotIn("完成", all_wordings)

    def test_responsibility_level_stays_conservative(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                self.assertEqual(claim["responsibility_level"], "participated")


class MedicalWritingExampleTest(unittest.TestCase):
    """医学写作样例：责任等级为 owned_component，表达要一致。"""

    def setUp(self):
        self.example = loads((ROOT / "data" / "fixtures" / "medical-writing-end-to-end-example.json").read_text(encoding="utf-8"))
        self.canonical_schema = loads((ROOT / "schemas" / "canonical-experience.schema.json").read_text(encoding="utf-8"))
        self.bullet_schema = loads((ROOT / "schemas" / "bullet-claim.schema.json").read_text(encoding="utf-8"))

    def test_user_input_matches_evidence(self):
        self.assertEqual(self.example["user_input"], self.example["evidence_records"][0]["source_text"])

    def test_extracted_facts_match_input(self):
        self.assertIn("write_review", self.example["extracted_facts"]["actions"])
        self.assertIn("summarize_guidelines", self.example["extracted_facts"]["actions"])
        # 不能推断未提及的数量、发表状态等
        self.assertNotIn("document_count", self.example["extracted_facts"]["scope"])

    def test_canonical_experience_validates(self):
        validate(instance=self.example["canonical_experience"], schema=self.canonical_schema)

    def test_bullet_claims_validate(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                with self.subTest(role_pack=role_pack, claim_id=claim["claim_id"]):
                    validate(instance=claim, schema=self.bullet_schema)

    def test_responsibility_level_consistent(self):
        levels = [claim["responsibility_level"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        self.assertTrue(all(level == "owned_component" for level in levels))

    def test_no_forbidden_outputs(self):
        all_wordings = " ".join(
            [claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        )
        for forbidden in self.example["forbidden_outputs"]:
            if "独立发表" in forbidden:
                self.assertNotIn("独立发表", all_wordings)
            if "主导" in forbidden:
                self.assertNotIn("主导", all_wordings)

    def test_unknowns_are_omitted(self):
        all_wordings = " ".join(
            [claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        )
        self.assertNotIn("篇", all_wordings)

    def test_evidence_traceability(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                self.assertEqual(claim["evidence_ids"], ["ev_005"])
                self.assertEqual(claim["experience_id"], "exp_005")


class ResponsibilityAmbiguousExampleTest(unittest.TestCase):
    """责任模糊样例：用户只说"负责"，系统不得擅自定级。"""

    def setUp(self):
        self.example = loads((ROOT / "data" / "fixtures" / "responsibility-ambiguous-end-to-end-example.json").read_text(encoding="utf-8"))
        self.canonical_schema = loads((ROOT / "schemas" / "canonical-experience.schema.json").read_text(encoding="utf-8"))
        self.bullet_schema = loads((ROOT / "schemas" / "bullet-claim.schema.json").read_text(encoding="utf-8"))

    def test_user_input_matches_evidence(self):
        self.assertEqual(self.example["user_input"], self.example["evidence_records"][0]["source_text"])

    def test_responsibility_ambiguity_flagged(self):
        self.assertIn("responsibility_ambiguity", self.example["bullet_claims"]["doctoral_v1"][0]["risk_flags"])
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                self.assertEqual(claim["verification_status"], "needs_confirmation")

    def test_responsibility_kept_conservative(self):
        # 责任模糊时默认降至 participated，而不是沿用"负责"
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                self.assertEqual(claim["responsibility_level"], "participated")

    def test_canonical_experience_validates(self):
        validate(instance=self.example["canonical_experience"], schema=self.canonical_schema)

    def test_bullet_claims_validate(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                with self.subTest(role_pack=role_pack, claim_id=claim["claim_id"]):
                    validate(instance=claim, schema=self.bullet_schema)

    def test_no_forbidden_outputs(self):
        all_wordings = " ".join(
            [claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        )
        for forbidden in self.example["forbidden_outputs"]:
            if "独立负责" in forbidden:
                self.assertNotIn("独立负责", all_wordings)
            if "主导" in forbidden:
                self.assertNotIn("主导", all_wordings)


class UserExaggerationExampleTest(unittest.TestCase):
    """用户夸大样例：系统必须降级而非放大声明。"""

    def setUp(self):
        self.example = loads((ROOT / "data" / "fixtures" / "user-exaggeration-end-to-end-example.json").read_text(encoding="utf-8"))
        self.canonical_schema = loads((ROOT / "schemas" / "canonical-experience.schema.json").read_text(encoding="utf-8"))
        self.bullet_schema = loads((ROOT / "schemas" / "bullet-claim.schema.json").read_text(encoding="utf-8"))

    def test_user_input_matches_evidence(self):
        self.assertEqual(self.example["user_input"], self.example["evidence_records"][0]["source_text"])

    def test_exaggeration_flagged(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                self.assertIn("potential_exaggeration", claim["risk_flags"])
                self.assertEqual(claim["verification_status"], "needs_confirmation")

    def test_no_fabricated_numbers(self):
        # 用户说"高影响因子"，但没给具体数值，系统不得猜测
        all_wordings = " ".join(
            [claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        )
        self.assertNotIn("影响因子", all_wordings)
        self.assertNotIn("第一作者", all_wordings)
        self.assertNotIn("高影响因子", all_wordings)

    def test_responsibility_downgraded(self):
        # 输入声称"独立主导"，但输出必须降至 participated 并待确认
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                self.assertEqual(claim["responsibility_level"], "participated")

    def test_canonical_experience_validates(self):
        validate(instance=self.example["canonical_experience"], schema=self.canonical_schema)

    def test_bullet_claims_validate(self):
        for role_pack, claims in self.example["bullet_claims"].items():
            for claim in claims:
                with self.subTest(role_pack=role_pack, claim_id=claim["claim_id"]):
                    validate(instance=claim, schema=self.bullet_schema)

    def test_no_forbidden_outputs(self):
        all_wordings = " ".join(
            [claim["wording"] for role_pack, claims in self.example["bullet_claims"].items() for claim in claims]
        )
        for forbidden in self.example["forbidden_outputs"]:
            if "独立主导" in forbidden:
                self.assertNotIn("独立主导", all_wordings)
            if "发表高影响因子" in forbidden:
                self.assertNotIn("发表高影响因子", all_wordings)


if __name__ == "__main__":
    unittest.main()
