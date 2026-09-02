import json
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "role-packs" / "pharmacovigilance_drug_safety_v1.json"


def test_pv_canonical_pack_is_schema_valid_and_has_boundary_cases():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas" / "role-pack.schema.json").read_text(encoding="utf-8"))

    validate(instance=pack, schema=schema)
    assert {case["input"]["case_type"] for case in pack["evaluation_cases"]} == {
        "positive", "transferable", "partial", "negative"
    }


def test_pv_canonical_cases_preserve_safety_ownership_boundaries():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    outputs = " ".join(
        output for case in pack["evaluation_cases"] for output in case["expected_output"]
    )

    assert all(
        prohibited not in outputs
        for prohibited in ("安全报告提交责任", "信号检测", "QPPV责任", "PV体系所有权", "监管沟通")
    )
    assert "ICSR 处理、签发或提交所有权" in pack["forbidden_claims"]
    assert "信号检测、信号评估或获益风险所有权" in pack["forbidden_claims"]
    assert "PV 体系、PSMF、QPPV 或最终质量责任" in pack["forbidden_claims"]
