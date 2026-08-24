import json
import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.three_tier_expression_system import ThreeTierExpressionSystem


def test_v32_golden_sample_three_tier_expression():
    """测试V3.2黄金样本的三档表达系统。"""
    print("测试三档表达系统与V3.2黄金样本")
    print("=" * 60)

    # 初始化系统
    system = ThreeTierExpressionSystem()

    # V3.2标准化经历（增强格式）
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
            "title": "研究助理",
            "responsibility_level": "participated",
            "personal_boundary": "在导师指导和团队协作下参与文献检索和筛选"
        },
        "background": "急性冠脉综合征患者对抗血小板治疗的临床争议",
        "problem_or_goal": "比较不同抗血小板药物在ACS患者中的疗效差异",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r", "endnote", "noteexpress"],
        "objects": ["medical_literature", "clinical_studies"],
        "workflow_steps": [
            "PICO框架构建",
            "多数据库检索策略执行",
            "两级筛选流程实施",
            "结构化数据提取"
        ],
        "quality_control": [
            "标题摘要初筛和全文复筛双重质量控制",
            "Cochrane RoB工具系统性偏倚风险评价",
            "标准化表格数据提取"
        ],
        "decisions_or_judgments": [
            "筛选分歧处理",
            "统计模型选择基于异质性"
        ],
        "difficulties": [
            "处理大量检索结果",
            "解决模糊纳入标准案例"
        ],
        "collaboration": ["课题组", "导师"],
        "artifacts": ["PRISMA流程图", "数据提取表"],
        "outputs": ["45篇纳入研究高质量结构化数据库", "统计分析结果"],
        "outcomes": ["第三作者论文投稿"],
        "insights": [
            "理解严谨方法学在证据综合中的重要性",
            "认识治疗效果异质性的临床意义"
        ],
        "capability_evidence": [
            "系统性文献检索能力",
            "PRISMA指南应用",
            "Cochrane RoB工具使用"
        ],
        "role_relevance": "直接相关于博士研究方法学要求",
        "research_interest_link": "连接到心血管二级预防优化兴趣",
        "scope": {
            "database_count": "3",
            "study_count": "45",
            "time_period": "2022-2024"
        },
        "status": "user_confirmed"
    }

    # V3.2内容计划
    v32_content_plan = {
        "experience_id": "v32_meta_analysis_001",
        "retain_reason": "核心Meta分析经历，符合博士申请要求",
        "priority": 10,
        "bullet_count_target": 8,
        "dimension_coverage": [
            "research_problem_identification", "literature_retrieval_and_screening",
            "systematic_review_methodology", "meta_analysis_statistics",
            "quality_assurance_measures", "research_workflow_execution",
            "critical_thinking_and_decisions", "team_collaboration",
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

    # 生成三档表达
    result = system.generate_three_tiers(
        canonical_experience=v32_experience,
        content_plan=v32_content_plan,
        target_role="doctoral_v1"
    )

    print(f"经历ID: {result.experience_id}")
    print(f"目标角色: {result.target_role}")
    print(f"保守版要点数: {len(result.conservative_claims)}")
    print(f"专业版要点数: {len(result.professional_claims)}")
    print(f"高竞争力版要点数: {len(result.high_impact_claims)}")

    # 显示一致性报告
    consistency = result.fact_consistency_report
    print(f"\n事实一致性: {'通过' if consistency['hard_facts_consistent'] else '失败'}")
    print(f"责任级别一致: {consistency['responsibility_level_consistent']}")
    print(f"证据ID一致: {consistency['evidence_ids_consistent']}")
    print(f"使用事实一致: {consistency['used_facts_consistent']}")

    if consistency["inconsistencies_found"]:
        print("发现的不一致:")
        for issue in consistency["inconsistencies_found"]:
            print(f"  - {issue}")

    # 显示各版本示例（前3个要点）
    print("\n各版本示例（前3个要点）:")

    print("\n保守版:")
    for i, claim in enumerate(result.conservative_claims[:3], 1):
        print(f"  {i}. {claim.wording}")

    print("\n专业版:")
    for i, claim in enumerate(result.professional_claims[:3], 1):
        print(f"  {i}. {claim.wording}")

    print("\n高竞争力版:")
    for i, claim in enumerate(result.high_impact_claims[:3], 1):
        print(f"  {i}. {claim.wording}")

    # 验证关键要求
    print("\n验证关键要求:")

    # 1. 事实一致性
    assert consistency["hard_facts_consistent"] == True, "事实一致性验证失败"
    print("事实一致性: 通过")

    # 2. 责任级别保护
    all_claims = result.conservative_claims + result.professional_claims + result.high_impact_claims
    responsibility_levels = set(claim.responsibility_level for claim in all_claims)
    assert len(responsibility_levels) == 1, f"责任级别不一致: {responsibility_levels}"
    assert "participated" in responsibility_levels, "责任级别不是participated"
    print("责任级别保护: 通过")

    # 3. 内容差异化
    conservative_text = " ".join([c.wording for c in result.conservative_claims])
    professional_text = " ".join([c.wording for c in result.professional_claims])
    high_impact_text = " ".join([c.wording for c in result.high_impact_claims])

    # 保守版应该更谨慎，专业版和高竞争力版应该更有价值表达
    conservative_participated_count = conservative_text.count("参与")
    professional_participated_count = professional_text.count("参与")
    high_impact_participated_count = high_impact_text.count("参与")

    # 保守版应该有最多的"参与"词汇
    assert conservative_participated_count >= professional_participated_count, "保守版参与词汇不够多"
    assert conservative_participated_count >= high_impact_participated_count, "保守版参与词汇不够多"
    print("表达差异化: 通过")

    # 4. 内容密度
    assert len(result.conservative_claims) >= 7, "保守版要点数不足"
    assert len(result.professional_claims) >= 7, "专业版要点数不足"
    assert len(result.high_impact_claims) >= 7, "高竞争力版要点数不足"
    print("内容密度: 通过")

    # 5. V3.2质量对标
    # 检查是否包含V3.2的关键元素
    v32_keywords = ["Meta分析", "系统检索", "质量评价", "结果解释", "第三作者", "45篇"]
    all_text = conservative_text + professional_text + high_impact_text

    found_keywords = [kw for kw in v32_keywords if kw in all_text]
    assert len(found_keywords) >= 3, f"V3.2关键词匹配不足: {found_keywords}"
    print("V3.2质量对标: 通过")

    print("\n" + "=" * 60)
    print("V3.2黄金样本三档表达系统测试完成！")
    print("所有关键要求验证通过")
    return True


if __name__ == "__main__":
    success = test_v32_golden_sample_three_tier_expression()
    if success:
        print("\n三档表达系统测试全部通过！")
    else:
        print("\n测试失败！")
        sys.exit(1)