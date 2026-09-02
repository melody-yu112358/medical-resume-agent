import json
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "role-packs" / "regulatory_medical_writing_v1.json"


def test_regulatory_medical_writing_canonical_pack_is_schema_valid_and_has_boundary_cases():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas" / "role-pack.schema.json").read_text(encoding="utf-8"))

    validate(instance=pack, schema=schema)
    assert {case["input"]["case_type"] for case in pack["evaluation_cases"]} == {
        "positive",
        "transferable",
        "partial",
        "negative",
    }


def test_regulatory_medical_writing_canonical_cases_preserve_authority_boundaries():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    bounded_outputs = " ".join(
        output
        for case in pack["evaluation_cases"]
        if case["input"]["case_type"] in {"positive", "transferable"}
        for output in case["expected_output"]
    )

    assert all(
        prohibited not in bounded_outputs
        for prohibited in ("最终提交责任", "法规策略所有权", "独立方案主笔", "CSR负责人", "客户所有权")
    )
    partial_output = pack["evaluation_cases"][2]["expected_output"][0]
    negative_output = pack["evaluation_cases"][3]["expected_output"][0]
    assert "尚缺独立方案主笔" in partial_output
    assert "不足以支持 Regulatory Medical Writing" in negative_output
    assert "IND、NDA、CTD 或其他法规提交所有权" in pack["forbidden_claims"]
    assert "法规策略、注册路径或监管机构沟通所有权" in pack["forbidden_claims"]
    assert "客户、供应商、预算或项目所有权" in pack["forbidden_claims"]
    assert "团队 mentoring、人员管理或工作分配责任" in pack["forbidden_claims"]
