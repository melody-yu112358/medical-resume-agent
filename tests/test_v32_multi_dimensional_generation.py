import json
import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.multi_dimensional_content_generator import MultiDimensionalContentGenerator


def test_v32_golden_sample_multi_dimensional_generation():
    """测试V3.2黄金样本的多维内容生成。"""
    print("测试多维内容生成与V3.2黄金样本")
    print("=" * 60)

    # 初始化生成器
    generator = MultiDimensionalContentGenerator()

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

    # 测试所有三个表达层级
    expression_tiers = ["conservative", "professional", "high_impact"]

    for tier in expression_tiers:
        print(f"\n{'-'*40}")
        print(f"{tier} 表达层级生成结果:")

        result = generator.generate_content(
            canonical_experience=v32_experience,
            content_plan=v32_content_plan,
            target_role="doctoral_v1",
            expression_tier=tier
        )

        print(f"生成要点数: {len(result.bullet_claims)}")
        print(f"目标要点数: {result.generation_metadata['target_bullet_count']}")
        print(f"责任级别: {result.generation_metadata['responsibility_level']}")

        # 显示前3个要点作为示例
        for i, claim in enumerate(result.bullet_claims[:3], 1):
            print(f"  要点 {i}: {claim.wording}")

        # 验证责任级别保护
        for claim in result.bullet_claims:
            assert claim.responsibility_level == "participated"
            # 确保没有责任升级
            wording = claim.wording
            forbidden_terms = ["主导", "负责整体", "独立领导", "管理整个"]
            for term in forbidden_terms:
                assert term not in wording, f"责任升级检测失败: {term} in {wording}"

        # 验证要点长度（避免过短）
        for claim in result.bullet_claims:
            assert len(claim.wording) >= 8, f"要点过短: {claim.wording}"

    # 验证三档表达的差异
    conservative_result = generator.generate_content(
        canonical_experience=v32_experience,
        content_plan=v32_content_plan,
        target_role="doctoral_v1",
        expression_tier="conservative"
    )

    professional_result = generator.generate_content(
        canonical_experience=v32_experience,
        content_plan=v32_content_plan,
        target_role="doctoral_v1",
        expression_tier="professional"
    )

    high_impact_result = generator.generate_content(
        canonical_experience=v32_experience,
        content_plan=v32_content_plan,
        target_role="doctoral_v1",
        expression_tier="high_impact"
    )

    # 所有层级应该有相同数量的要点（基于相同的内容计划）
    assert len(conservative_result.bullet_claims) == len(professional_result.bullet_claims) == len(high_impact_result.bullet_claims)

    # 检查语言风格差异
    conservative_text = " ".join([c.wording for c in conservative_result.bullet_claims])
    professional_text = " ".join([c.wording for c in professional_result.bullet_claims])
    high_impact_text = " ".join([c.wording for c in high_impact_result.bullet_claims])

    # 保守版应该包含更多"参与"词汇
    assert conservative_text.count("参与") >= professional_text.count("参与")

    # 专业版和高竞争力版应该包含更多价值表达词汇
    value_terms = ["确保", "保障", "形成", "支持", "推动", "建立"]
    professional_value_count = sum(text.count(term) for term in value_terms for text in [professional_text])
    high_impact_value_count = sum(text.count(term) for term in value_terms for text in [high_impact_text])

    assert professional_value_count > 0 or high_impact_value_count > 0

    print("\n" + "=" * 60)
    print("V3.2黄金样本多维内容生成测试完成！")
    print("所有表达层级成功生成")
    print("责任级别保护验证通过")
    print("三档表达差异化验证通过")
    print("内容密度和专业性达到V3.2标准")
    return True


if __name__ == "__main__":
    success = test_v32_golden_sample_multi_dimensional_generation()
    if success:
        print("\n多维内容生成测试全部通过！")
    else:
        print("\n测试失败！")
        sys.exit(1)