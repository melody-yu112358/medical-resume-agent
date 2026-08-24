import json
import pytest
from pathlib import Path

# 添加src到路径
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.three_tier_expression_system import ThreeTierExpressionSystem, ThreeTierExpressionResult


def test_three_tier_system_initialization():
    """测试三档表达系统初始化。"""
    system = ThreeTierExpressionSystem()
    assert hasattr(system, 'content_generator')
    assert system.content_generator is not None


def test_basic_three_tier_generation():
    """测试基本三档表达生成。"""
    system = ThreeTierExpressionSystem()

    # 最小化经历
    minimal_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"],
        "status": "user_confirmed"
    }

    minimal_content_plan = {
        "experience_id": "test_001",
        "retain_reason": "基础研究经历",
        "priority": 5,
        "bullet_count_target": 3,
        "dimension_coverage": ["literature_retrieval_and_screening", "systematic_review_methodology"],
        "representative_contribution": "文献检索",
        "methodology_bullet": "Focus on literature retrieval",
        "quality_control_bullet": "Emphasize systematic approach",
        "results_or_outputs_bullet": "Present research contribution",
        "role_value_bullet": "Highlight research skills",
        "content_to_exclude": [],
        "suitable_for_resume": True,
        "evidence_ids": ["ev_001"]
    }

    result = system.generate_three_tiers(
        canonical_experience=minimal_experience,
        content_plan=minimal_content_plan,
        target_role="doctoral_v1"
    )

    # 验证结果结构
    assert isinstance(result, ThreeTierExpressionResult)
    assert result.experience_id == "test_001"
    assert result.target_role == "doctoral_v1"

    # 所有三个版本都应该有内容
    assert len(result.conservative_claims) > 0
    assert len(result.professional_claims) > 0
    assert len(result.high_impact_claims) > 0

    # 验证一致性报告
    consistency = result.fact_consistency_report
    assert isinstance(consistency, dict)
    assert "hard_facts_consistent" in consistency
    assert "responsibility_level_consistent" in consistency
    assert "evidence_ids_consistent" in consistency
    assert "used_facts_consistent" in consistency


def test_v32_three_tier_generation():
    """测试V3.2样例三档表达生成。"""
    system = ThreeTierExpressionSystem()

    v32_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "v32_meta_analysis_001",
        "evidence_ids": ["ev_v32_001"],
        "context": {
            "domain": "clinical_research",
            "setting": "research_project",
            "topic": "心血管Meta分析"
        },
        "role": {
            "responsibility_level": "participated",
            "personal_boundary": "在导师指导和团队协作下参与文献检索和筛选"
        },
        "background": "急性冠脉综合征患者对抗血小板治疗的临床争议",
        "problem_or_goal": "比较不同抗血小板药物在ACS患者中的疗效差异",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r", "endnote"],
        "workflow_steps": ["PICO框架构建", "多数据库检索策略执行"],
        "quality_control": ["标题摘要初筛和全文复筛两级筛选", "Cochrane RoB工具偏倚风险评价"],
        "outcomes": ["第三作者论文投稿"],
        "scope": {"study_count": "45"},
        "status": "user_confirmed"
    }

    v32_content_plan = {
        "experience_id": "v32_meta_analysis_001",
        "retain_reason": "核心Meta分析经历，符合博士申请要求",
        "priority": 10,
        "bullet_count_target": 8,
        "dimension_coverage": [
            "research_problem_identification", "literature_retrieval_and_screening",
            "systematic_review_methodology", "meta_analysis_statistics",
            "quality_assurance_measures", "research_workflow_execution",
            "research_outcomes_and_impact", "scientific_insights"
        ],
        "representative_contribution": "统计Meta分析和结果解释",
        "methodology_bullet": "Focus on PICO framework and systematic search",
        "quality_control_bullet": "Emphasize PRISMA compliance and dual screening",
        "results_or_outputs_bullet": "Present study database and manuscript contribution",
        "role_value_bullet": "Highlight research methodology competence",
        "content_to_exclude": ["独立领导声明", "未验证的影响声明"],
        "suitable_for_resume": True,
        "evidence_ids": ["ev_v32_001"]
    }

    result = system.generate_three_tiers(
        canonical_experience=v32_experience,
        content_plan=v32_content_plan,
        target_role="doctoral_v1"
    )

    # V3.2应该生成丰富的内容
    assert len(result.conservative_claims) >= 5
    assert len(result.professional_claims) >= 5
    assert len(result.high_impact_claims) >= 5

    # 所有版本应该有相同数量的要点（基于相同的内容计划）
    assert len(result.conservative_claims) == len(result.professional_claims) == len(result.high_impact_claims)

    # 验证事实一致性
    consistency = result.fact_consistency_report
    assert consistency["hard_facts_consistent"] == True
    assert consistency["responsibility_level_consistent"] == True
    assert consistency["evidence_ids_consistent"] == True
    assert consistency["used_facts_consistent"] == True

    # 验证责任级别保护
    for claim in result.conservative_claims + result.professional_claims + result.high_impact_claims:
        assert claim.responsibility_level == "participated"


def test_fact_consistency_validation():
    """测试事实一致性验证。"""
    system = ThreeTierExpressionSystem()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001", "ev_002"],
        "context": {"domain": "clinical_research", "topic": "Meta分析研究"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature", "screen_studies"],
        "methods": ["systematic_review"],
        "tools": ["spss"],
        "status": "user_confirmed"
    }

    content_plan = {
        "experience_id": "test_001",
        "bullet_count_target": 3,
        "dimension_coverage": ["literature_retrieval_and_screening", "systematic_review_methodology"],
        "evidence_ids": ["ev_001", "ev_002"]
    }

    result = system.generate_three_tiers(
        canonical_experience=experience,
        content_plan=content_plan,
        target_role="doctoral_v1"
    )

    # 直接验证一致性
    is_consistent = system.validate_three_tiers_consistency(result, experience)
    assert is_consistent == True

    # 验证一致性报告的详细信息
    report = result.fact_consistency_report
    details = report["validation_details"]
    assert details["total_claims"] == len(result.conservative_claims + result.professional_claims + result.high_impact_claims)
    assert details["expected_responsibility_level"] == "participated"
    assert details["expected_evidence_count"] == 2


def test_responsibility_level_consistency():
    """测试责任级别一致性。"""
    system = ThreeTierExpressionSystem()

    # 参与级别经历
    participated_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "participated_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "status": "user_confirmed"
    }

    content_plan = {
        "experience_id": "participated_001",
        "bullet_count_target": 2,
        "dimension_coverage": ["literature_retrieval_and_screening"],
        "evidence_ids": ["ev_001"]
    }

    result = system.generate_three_tiers(
        canonical_experience=participated_experience,
        content_plan=content_plan,
        target_role="doctoral_v1"
    )

    # 所有三个版本都应该保持"participated"责任级别
    all_claims = result.conservative_claims + result.professional_claims + result.high_impact_claims
    responsibility_levels = set(claim.responsibility_level for claim in all_claims)
    assert len(responsibility_levels) == 1
    assert "participated" in responsibility_levels

    # 即使是高竞争力版也不应该升级责任级别
    for claim in result.high_impact_claims:
        assert claim.responsibility_level == "participated"


def test_evidence_binding_consistency():
    """测试证据绑定一致性。"""
    system = ThreeTierExpressionSystem()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_test_001", "ev_test_002"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "status": "user_confirmed"
    }

    content_plan = {
        "experience_id": "test_001",
        "bullet_count_target": 2,
        "dimension_coverage": ["literature_retrieval_and_screening"],
        "evidence_ids": ["ev_test_001", "ev_test_002"]
    }

    result = system.generate_three_tiers(
        canonical_experience=experience,
        content_plan=content_plan,
        target_role="doctoral_v1"
    )

    # 所有声明都应该绑定到相同的证据ID
    expected_evidence = {"ev_test_001", "ev_test_002"}
    for claim in result.conservative_claims + result.professional_claims + result.high_impact_claims:
        assert set(claim.evidence_ids) == expected_evidence


def test_to_dict_conversion():
    """测试字典转换。"""
    system = ThreeTierExpressionSystem()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "status": "user_confirmed"
    }

    content_plan = {
        "experience_id": "test_001",
        "bullet_count_target": 2,
        "dimension_coverage": ["literature_retrieval_and_screening"],
        "evidence_ids": ["ev_001"]
    }

    result = system.generate_three_tiers(
        canonical_experience=experience,
        content_plan=content_plan,
        target_role="doctoral_v1"
    )

    # 测试ThreeTierExpressionResult to_dict
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert "experience_id" in result_dict
    assert "target_role" in result_dict
    assert "conservative_claims" in result_dict
    assert "professional_claims" in result_dict
    assert "high_impact_claims" in result_dict
    assert "fact_consistency_report" in result_dict

    # 测试BulletClaim to_dict（通过claims）
    conservative_dict = result_dict["conservative_claims"][0]
    assert "claim_id" in conservative_dict
    assert "wording" in conservative_dict
    assert "responsibility_level" in conservative_dict


if __name__ == "__main__":
    # 运行测试
    test_three_tier_system_initialization()
    test_basic_three_tier_generation()
    test_v32_three_tier_generation()
    test_fact_consistency_validation()
    test_responsibility_level_consistency()
    test_evidence_binding_consistency()
    test_to_dict_conversion()
    print("所有三档表达系统测试通过！")