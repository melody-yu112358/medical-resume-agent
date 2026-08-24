import json
import pytest
from pathlib import Path

# 添加src到路径
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.semantic_claim_gate import SemanticClaimGateService, SemanticClaimGateResult


def test_semantic_claim_gate_initialization():
    """测试语义分层Claim Gate初始化。"""
    service = SemanticClaimGateService()
    assert hasattr(service, 'hard_fact_patterns')
    assert hasattr(service, 'professional_context_patterns')
    assert hasattr(service, 'role_value_patterns')


def test_v32_claim_validation():
    """测试V3.2样例声明验证。"""
    service = SemanticClaimGateService()

    v32_claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_v32_001",
        "experience_id": "v32_meta_analysis_001",
        "role_pack": "doctoral_v1",
        "wording": "系统参与Meta分析流程，完成文献检索、筛选和数据提取，并参与统计分析与结果解释",
        "used_facts": ["actions:retrieve_literature", "actions:screen_studies", "actions:extract_data"],
        "evidence_ids": ["ev_v32_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    v32_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "v32_meta_analysis_001",
        "evidence_ids": ["ev_v32_001"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r"],
        "outcomes": ["第三作者论文投稿"],
        "scope": {"study_count": "45"},
        "status": "user_confirmed"
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=v32_claim,
        canonical_experience=v32_experience
    )

    # V3.2声明在不升级责任的情况下应该通过验证
    assert isinstance(result, SemanticClaimGateResult)
    assert result.hard_facts_valid == True
    assert result.status == "ready"


def test_responsibility_upgrade_detection():
    """测试责任升级检测。"""
    service = SemanticClaimGateService()

    # 声明中使用"主导"但责任级别是"participated"
    upgrade_claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_upgrade_001",
        "experience_id": "test_001",
        "role_pack": "doctoral_v1",
        "wording": "主导Meta分析的文献检索工作",
        "used_facts": ["actions:retrieve_literature"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "status": "user_confirmed"
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=upgrade_claim,
        canonical_experience=experience
    )

    # 应该检测到责任升级并拒绝
    assert result.hard_facts_valid == False
    assert result.status == "rejected"
    assert any("responsibility_upgrade" in check for check in result.failed_checks)


@pytest.mark.parametrize(
    ("canonical_role", "claim_level", "wording", "expected_status"),
    [
        ({"responsibility_level": "participated"}, "participated", "独立完成文献检索", "rejected"),
        ({"responsibility_level": "participated"}, "project_owner", "主导文献检索", "rejected"),
        ({"responsibility_level": "owned_component"}, "owned_component", "独立完成统计分析", "rejected"),
        (
            {"responsibility_level": "owned_component", "personal_boundary": "独立完成统计分析模块"},
            "owned_component",
            "独立完成统计分析模块",
            "ready",
        ),
    ],
)
def test_canonical_responsibility_is_authoritative(
    canonical_role, claim_level, wording, expected_status
):
    service = SemanticClaimGateService()
    claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_boundary_001",
        "experience_id": "test_001",
        "role_pack": "doctoral_v1",
        "wording": wording,
        "used_facts": ["actions:retrieve_literature"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": claim_level,
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None,
    }
    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": canonical_role,
        "actions": ["retrieve_literature", "analyze_data"],
        "status": "user_confirmed",
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=claim, canonical_experience=experience
    )

    assert result.status == expected_status


def test_numbers_consistency_validation():
    """测试数字一致性验证。"""
    service = SemanticClaimGateService()

    # 声明中提到"50篇"但标准化经历中是"45篇"
    inconsistent_claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_numbers_001",
        "experience_id": "test_001",
        "role_pack": "doctoral_v1",
        "wording": "维护50篇纳入研究的高质量结构化数据库",
        "used_facts": ["outputs:database"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "scope": {"study_count": "45"},
        "status": "user_confirmed"
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=inconsistent_claim,
        canonical_experience=experience
    )

    # 应该检测到数字不一致
    assert result.hard_facts_valid == False
    assert any("numbers_mismatch" in check for check in result.failed_checks)


def test_role_value_allowance():
    """测试岗位价值表达允许。"""
    service = SemanticClaimGateService()

    # 包含有力价值表达的声明
    value_claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_value_001",
        "experience_id": "test_001",
        "role_pack": "doctoral_v1",
        "wording": "确保文献检索的全面性和准确性，保障纳入研究的质量一致性",
        "used_facts": ["actions:retrieve_literature", "actions:screen_studies"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature", "screen_studies"],
        "status": "user_confirmed"
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=value_claim,
        canonical_experience=experience
    )

    # 价值表达应该被允许
    assert result.role_value_valid == True
    assert result.hard_facts_valid == True
    assert result.status == "ready"


def test_tools_methods_consistency():
    """测试工具和方法一致性。"""
    service = SemanticClaimGateService()

    # 声明中提到未确认的工具
    inconsistent_claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_tools_001",
        "experience_id": "test_001",
        "role_pack": "doctoral_v1",
        "wording": "使用Python进行异质性评价",
        "used_facts": ["methods:meta_analysis"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "methods": ["meta_analysis"],
        "tools": ["spss", "r"],  # 没有Python
        "status": "user_confirmed"
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=inconsistent_claim,
        canonical_experience=experience
    )

    # 应该检测到工具不一致
    assert result.hard_facts_valid == False
    assert any("tools_methods_mismatch" in check for check in result.failed_checks)


def test_publications_consistency():
    """测试出版物一致性。"""
    service = SemanticClaimGateService()

    # 声明中提到未确认的署名位置
    inconsistent_claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_pub_001",
        "experience_id": "test_001",
        "role_pack": "doctoral_v1",
        "wording": "作为第一作者参与撰写论文",
        "used_facts": ["outcomes:publication"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "outcomes": ["第三作者论文投稿"],  # 第三作者，不是第一作者
        "status": "user_confirmed"
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=inconsistent_claim,
        canonical_experience=experience
    )

    # 应该检测到出版物信息不一致
    assert result.hard_facts_valid == False
    assert any("publications_mismatch" in check for check in result.failed_checks)


def test_to_dict_conversion():
    """测试字典转换。"""
    service = SemanticClaimGateService()

    claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_test_001",
        "experience_id": "test_001",
        "role_pack": "doctoral_v1",
        "wording": "参与文献检索工作",
        "used_facts": ["actions:retrieve_literature"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "status": "user_confirmed"
    }

    result = service.validate_claim_semantic_layers(
        bullet_claim=claim,
        canonical_experience=experience
    )

    # 测试SemanticClaimGateResult to_dict
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert "status" in result_dict
    assert "hard_facts_valid" in result_dict
    assert "professional_context_valid" in result_dict
    assert "role_value_valid" in result_dict
    assert "future_interests_valid" in result_dict
    assert "failed_checks" in result_dict
    assert "risk_flags" in result_dict


if __name__ == "__main__":
    # 运行测试
    test_semantic_claim_gate_initialization()
    test_v32_claim_validation()
    test_responsibility_upgrade_detection()
    test_numbers_consistency_validation()
    test_role_value_allowance()
    test_tools_methods_consistency()
    test_publications_consistency()
    test_to_dict_conversion()
    print("所有语义分层Claim Gate测试通过！")
