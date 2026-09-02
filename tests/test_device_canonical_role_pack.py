import json
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "role-packs" / "medical_device_clinical_application_specialist_v1.json"


def test_device_canonical_pack_is_schema_valid_and_has_boundary_cases():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas" / "role-pack.schema.json").read_text(encoding="utf-8"))

    validate(instance=pack, schema=schema)
    assert {case["input"]["case_type"] for case in pack["evaluation_cases"]} == {
        "positive",
        "transferable",
        "partial",
        "negative",
    }


def test_device_canonical_cases_preserve_clinical_and_commercial_boundaries():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    outputs = " ".join(
        output for case in pack["evaluation_cases"] for output in case["expected_output"]
    )

    assert all(
        prohibited not in outputs
        for prohibited in ("临床决策", "手术责任", "销售指标", "产品路线图", "客户所有权")
    )
    assert "临床决策或患者照护所有权" in pack["forbidden_claims"]
    assert "产品路线图或研发所有权" in pack["forbidden_claims"]
    assert "销售KPI、收入、配额、区域或商业策略所有权" in pack["forbidden_claims"]
