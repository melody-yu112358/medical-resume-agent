import json
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "role-packs" / "clinical_data_management_v1.json"


def test_cdm_canonical_pack_is_schema_valid_and_has_boundary_cases():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas" / "role-pack.schema.json").read_text(encoding="utf-8"))

    validate(instance=pack, schema=schema)
    assert {case["input"]["case_type"] for case in pack["evaluation_cases"]} == {
        "positive", "transferable", "partial", "negative"
    }


def test_cdm_canonical_cases_preserve_data_management_boundaries():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    outputs = " ".join(
        output for case in pack["evaluation_cases"] for output in case["expected_output"]
    )

    assert all(
        prohibited not in outputs
        for prohibited in ("数据库锁定", "数据管理负责人", "EDC配置", "项目预算")
    )
    assert "独立 EDC 建库或配置权" in pack["forbidden_claims"]
    assert "最终数据交付所有权" in pack["forbidden_claims"]
