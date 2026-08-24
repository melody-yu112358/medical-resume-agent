from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .bullet_composer import BulletClaim
from .multi_dimensional_content_generator import MultiDimensionalContentGenerator


@dataclass(frozen=True)
class ThreeTierExpressionResult:
    """三档表达系统的结果，包含三个版本的要点声明。"""

    experience_id: str
    target_role: str
    conservative_claims: List[BulletClaim]
    professional_claims: List[BulletClaim]
    high_impact_claims: List[BulletClaim]
    fact_consistency_report: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "target_role": self.target_role,
            "conservative_claims": [claim.to_dict() for claim in self.conservative_claims],
            "professional_claims": [claim.to_dict() for claim in self.professional_claims],
            "high_impact_claims": [claim.to_dict() for claim in self.high_impact_claims],
            "fact_consistency_report": self.fact_consistency_report
        }


class ThreeTierExpressionSystem:
    """在相同事实基础上生成三档表达的系统。

    此服务实现以下要求：
    - 同一组标准化事实和同一份内容计划生成三个版本
    - 保守版：责任边界最严格，适合医院、人事审核和证据较少场景
    - 专业版：默认推荐，内容丰富、自信、专业，接近V3.2专业版
    - 高竞争力版：接近ASu式强表达，最大化候选人定位、项目复杂性和岗位价值
    - 三个版本不得分别自由重新发明内容，只改变表达力度、信息顺序、句式、价值解释、岗位匹配
    - 增加版本一致性测试，确保三版中的硬事实完全相同
    """

    def __init__(self, dimensions_config_path: Optional[str | Path] = None):
        """使用医学知识维度初始化。"""
        self.content_generator = MultiDimensionalContentGenerator(dimensions_config_path)

    def generate_three_tiers(
        self,
        *,
        canonical_experience: Dict[str, Any],
        content_plan: Dict[str, Any],
        target_role: str
    ) -> ThreeTierExpressionResult:
        """生成三档表达版本。

        Args:
            canonical_experience: 确认的标准化经历记录
            content_plan: 内容计划字典
            target_role: 目标角色方向

        Returns:
            三档表达结果
        """
        # 验证输入
        if not canonical_experience:
            raise ValueError("需要提供标准化经历记录")

        if not content_plan:
            raise ValueError("需要提供内容计划")

        experience_id = canonical_experience.get("experience_id", "unknown")

        # Find the experience-specific plan
        experience_specific_plan = content_plan.copy()
        experience_plans = content_plan.get("experience_plans", [])
        matched = False
        for exp_plan in experience_plans:
            if exp_plan.get("experience_id") == experience_id:
                # Use the experience-specific bullet count target
                experience_specific_plan["bullet_count_target"] = exp_plan.get("bullet_count_target", 5)
                matched = True
                break

        # 提供了经历计划但未匹配到当前经历时，才回退到默认目标数；
        # 未提供任何经历计划时保留调用方指定的目标数。
        if not matched and experience_plans:
            experience_specific_plan["bullet_count_target"] = 5

        # 使用相同的事实和内容计划生成三个版本
        conservative_result = self.content_generator.generate_content(
            canonical_experience=canonical_experience,
            content_plan=experience_specific_plan,
            target_role=target_role,
            expression_tier="conservative"
        )

        professional_result = self.content_generator.generate_content(
            canonical_experience=canonical_experience,
            content_plan=experience_specific_plan,
            target_role=target_role,
            expression_tier="professional"
        )

        high_impact_result = self.content_generator.generate_content(
            canonical_experience=canonical_experience,
            content_plan=experience_specific_plan,
            target_role=target_role,
            expression_tier="high_impact"
        )

        # 验证事实一致性
        fact_consistency_report = self._validate_fact_consistency(
            conservative_result.bullet_claims,
            professional_result.bullet_claims,
            high_impact_result.bullet_claims,
            canonical_experience
        )

        return ThreeTierExpressionResult(
            experience_id=experience_id,
            target_role=target_role,
            conservative_claims=conservative_result.bullet_claims,
            professional_claims=professional_result.bullet_claims,
            high_impact_claims=high_impact_result.bullet_claims,
            fact_consistency_report=fact_consistency_report
        )

    def _validate_fact_consistency(
        self,
        conservative_claims: List[BulletClaim],
        professional_claims: List[BulletClaim],
        high_impact_claims: List[BulletClaim],
        canonical_experience: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证三个版本的事实一致性。"""
        report = {
            "hard_facts_consistent": True,
            "responsibility_level_consistent": True,
            "evidence_ids_consistent": True,
            "used_facts_consistent": True,
            "inconsistencies_found": [],
            "validation_details": {}
        }

        # 提取所有声明
        all_claims = conservative_claims + professional_claims + high_impact_claims

        # 验证责任级别一致性
        responsibility_levels = set(claim.responsibility_level for claim in all_claims)
        if len(responsibility_levels) > 1:
            report["responsibility_level_consistent"] = False
            report["inconsistencies_found"].append(f"责任级别不一致: {responsibility_levels}")

        # 验证证据ID一致性
        expected_evidence_ids = set(canonical_experience.get("evidence_ids", []))
        for claim in all_claims:
            claim_evidence_ids = set(claim.evidence_ids)
            if claim_evidence_ids != expected_evidence_ids:
                report["evidence_ids_consistent"] = False
                report["inconsistencies_found"].append(
                    f"证据ID不一致: 期望{expected_evidence_ids}, 实际{claim_evidence_ids}"
                )
                break

        # 验证使用的事实一致性（基于标准化经历）
        expected_facts = self._extract_expected_facts(canonical_experience)
        for claim in all_claims:
            claim_used_facts = set(claim.used_facts)
            # 检查是否所有使用的事实都在预期范围内
            unexpected_facts = claim_used_facts - expected_facts
            if unexpected_facts:
                report["used_facts_consistent"] = False
                report["inconsistencies_found"].append(
                    f"使用了未预期的事实: {unexpected_facts}"
                )

        # 总体一致性
        report["hard_facts_consistent"] = (
            report["responsibility_level_consistent"] and
            report["evidence_ids_consistent"] and
            report["used_facts_consistent"]
        )

        # 添加验证详情
        report["validation_details"] = {
            "total_claims": len(all_claims),
            "conservative_claims": len(conservative_claims),
            "professional_claims": len(professional_claims),
            "high_impact_claims": len(high_impact_claims),
            "expected_responsibility_level": canonical_experience.get("role", {}).get("responsibility_level", "unknown"),
            "expected_evidence_count": len(expected_evidence_ids),
            "expected_facts_count": len(expected_facts)
        }

        return report

    def _extract_expected_facts(self, canonical_experience: Dict[str, Any]) -> Set[str]:
        """从标准化经历中提取预期的事实集合。"""
        expected_facts = set()

        # 添加所有可能的数组字段的事实
        array_fields = [
            "actions", "methods", "tools", "objects", "collaboration",
            "artifacts", "outcomes", "workflow_steps", "quality_control",
            "decisions_or_judgments", "difficulties", "insights",
            "capability_evidence", "outputs", "clinical_skills",
            "basic_operations", "auxiliary_exams", "databases_used",
        ]
        for field in array_fields:
            items = canonical_experience.get(field, [])
            for item in items:
                expected_facts.add(f"{field}:{item}")

        # 字符串事实（问题/目标/背景/结论等）
        for field in ["problem_or_goal", "background", "key_findings", "recommendations",
                      "research_inspiration", "results_interpretation", "data_extraction"]:
            value = canonical_experience.get(field)
            if isinstance(value, str) and value.strip():
                expected_facts.add(f"{field}:{value}")

        # 添加上下文事实
        context = canonical_experience.get("context", {})
        for key, value in context.items():
            if value:
                expected_facts.add(f"context.{key}:{value}")

        # 添加角色事实
        role = canonical_experience.get("role", {})
        for key, value in role.items():
            if value:
                expected_facts.add(f"role.{key}:{value}")

        # 添加范围事实（scope是一个字典）
        scope = canonical_experience.get("scope", {})
        for key, value in scope.items():
            expected_facts.add(f"scope.{key}:{value}")  # 注意这里使用 scope.key:value 而不是 scope:key=value

        return expected_facts

    def validate_three_tiers_consistency(
        self,
        three_tier_result: ThreeTierExpressionResult,
        canonical_experience: Dict[str, Any]
    ) -> bool:
        """验证三档表达结果的一致性。"""
        validation_report = self._validate_fact_consistency(
            three_tier_result.conservative_claims,
            three_tier_result.professional_claims,
            three_tier_result.high_impact_claims,
            canonical_experience
        )
        return validation_report["hard_facts_consistent"]


# 示例用法
if __name__ == "__main__":
    # 测试三档表达系统
    system = ThreeTierExpressionSystem()

    # V3.2样例经历
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

    print("三档表达系统结果:")
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

    # 显示各版本示例
    print("\n各版本示例:")
    if result.conservative_claims:
        print(f"保守版: {result.conservative_claims[0].wording}")
    if result.professional_claims:
        print(f"专业版: {result.professional_claims[0].wording}")
    if result.high_impact_claims:
        print(f"高竞争力版: {result.high_impact_claims[0].wording}")