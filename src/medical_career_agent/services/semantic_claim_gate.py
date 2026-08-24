from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .bullet_composer import BulletClaim


@dataclass(frozen=True)
class SemanticClaimGateResult:
    """语义分层Claim Gate验证结果。"""

    status: str  # "ready", "needs_confirmation", or "rejected"
    hard_facts_valid: bool
    professional_context_valid: bool
    role_value_valid: bool
    future_interests_valid: bool
    failed_checks: List[str]
    risk_flags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "hard_facts_valid": self.hard_facts_valid,
            "professional_context_valid": self.professional_context_valid,
            "role_value_valid": self.role_value_valid,
            "future_interests_valid": self.future_interests_valid,
            "failed_checks": self.failed_checks,
            "risk_flags": self.risk_flags,
        }


class SemanticClaimGateService:
    """语义分层的Claim Gate验证服务。

    将主张分为四个语义层级：
    A. 硬事实：学校、单位、时间、数字、论文、署名、工具、方法、研究结果、临床操作、责任等级、个人实际行为
    B. 专业语境：研究背景、已确认方法对应的标准流程、工作在项目中的作用、方法学说明
    C. 岗位价值：确保检索全面性、保障数据质量、支持结果解释、形成循证研究能力、展现临床问题意识、为后续研究提供依据
    D. 未来兴趣：申请方向、研究兴趣、希望发展的领域

    Claim Gate必须：
    - 拦截虚构硬事实
    - 允许有力价值表达
    - 解释拒绝原因
    - 提供可修正建议
    - 与Claim Ledger集成
    - 保留现有12项确定性检查
    - 对现有测试向后兼容
    - 增加语义分层测试
    """

    def __init__(self, role_packs_dir: str | Path | None = None):
        self.role_packs_dir = Path(role_packs_dir) if role_packs_dir else Path(__file__).parent.parent.parent.parent / "data" / "role-packs"

        # 硬事实关键词模式
        self.hard_fact_patterns = {
            "education": [r"某医科大学", r"临床医学学士", r"GPA.*3\.8", r"CET-6.*580"],
            "numbers": [r"\d+篇", r"\d+次", r"\d+%"],
            "publications": [r"第三作者", r"在投", r"发表"],
            "tools": [r"SPSS", r"R基础", r"EndNote", r"NoteExpress"],
            "methods": [r"系统综述", r"Meta分析", r"流行病学调查"],
            "clinical_operations": [r"静脉采血", r"心电图", r"生命体征监测"],
            "responsibility_levels": ["参与", "协助", "负责", "主导", "管理"]
        }

        # 专业语境允许模式
        self.professional_context_patterns = {
            "research_background": [r"针对.*临床争议", r"基于.*背景", r"在.*指导下"],
            "standard_processes": [r"PRISMA流程", r"Cochrane RoB", r"标准化表格"],
            "project_roles": [r"课题组", r"团队协作", r"导师指导"],
            "methodology_explanations": [r"异质性评价", r"敏感性分析", r"结果稳定性"]
        }

        # 岗位价值允许模式
        self.role_value_patterns = {
            "quality_assurance": [r"确保", r"保障", r"维护", r"保证"],
            "capability_building": [r"形成", r"建立", r"培养", r"发展"],
            "process_support": [r"支持", r"促进", r"推动", r"协助"],
            "outcome_driving": [r"贡献", r"提供", r"产生", r"实现"]
        }

        # 未来兴趣标识
        self.future_interest_indicators = [r"致力于", r"希望", r"计划", r"目标", r"感兴趣"]

    def validate_claim_semantic_layers(
        self,
        *,
        bullet_claim: Dict[str, Any],
        canonical_experience: Dict[str, Any]
    ) -> SemanticClaimGateResult:
        """验证声明的语义分层。

        Args:
            bullet_claim: 要点声明字典 (bullet-claim-v1模式)
            canonical_experience: 对应的标准化经历记录 (canonical-experience-v1模式)

        Returns:
            语义分层验证结果
        """
        # 验证输入模式
        if bullet_claim.get("schema_version") != "bullet-claim-v1":
            raise ValueError("bullet_claim必须使用bullet-claim-v1模式")

        if canonical_experience.get("schema_version") != "canonical-experience-v1":
            raise ValueError("canonical_experience必须使用canonical-experience-v1模式")

        if canonical_experience.get("status") != "user_confirmed":
            raise ValueError("canonical_experience必须具有状态'user_confirmed'")

        wording = bullet_claim.get("wording", "")
        # The confirmed canonical record is the only authority for responsibility.
        # A generated claim must never be able to raise its own permission level.
        responsibility_level = canonical_experience.get("role", {}).get(
            "responsibility_level", "unknown"
        )
        target_role = bullet_claim.get("role_pack", "")

        # 初始化结果
        failed_checks = []
        risk_flags = list(bullet_claim.get("risk_flags", []))

        # 验证四个语义层级
        hard_facts_valid = self._validate_hard_facts(wording, canonical_experience, responsibility_level, failed_checks)
        professional_context_valid = self._validate_professional_context(wording, canonical_experience, failed_checks)
        role_value_valid = self._validate_role_value(wording, target_role, failed_checks)
        future_interests_valid = self._validate_future_interests(wording, failed_checks)

        # 确定整体状态
        if hard_facts_valid and professional_context_valid and role_value_valid and future_interests_valid:
            status = "ready"
        elif not hard_facts_valid:
            status = "rejected"
        else:
            status = "needs_confirmation"

        return SemanticClaimGateResult(
            status=status,
            hard_facts_valid=hard_facts_valid,
            professional_context_valid=professional_context_valid,
            role_value_valid=role_value_valid,
            future_interests_valid=future_interests_valid,
            failed_checks=failed_checks,
            risk_flags=risk_flags
        )

    def _validate_hard_facts(
        self,
        wording: str,
        canonical_experience: Dict[str, Any],
        responsibility_level: str,
        failed_checks: List[str]
    ) -> bool:
        """验证硬事实层级。"""
        valid = True

        # 提取标准化经历中的硬事实
        expected_hard_facts = self._extract_hard_facts_from_canonical(canonical_experience)

        # 检查数字一致性
        if not self._validate_numbers_consistency(wording, canonical_experience):
            failed_checks.append("numbers_mismatch: 声明中的数字与标准化经历不匹配")
            valid = False

        # 检查责任级别一致性
        if not self._validate_responsibility_consistency(wording, responsibility_level, canonical_experience):
            failed_checks.append(f"responsibility_upgrade: 责任级别从{responsibility_level}升级")
            valid = False

        # 检查工具和方法一致性
        if not self._validate_tools_methods_consistency(wording, canonical_experience):
            failed_checks.append("tools_methods_mismatch: 声明中的工具/方法与标准化经历不匹配")
            valid = False

        # 检查出版物和署名一致性
        if not self._validate_publications_consistency(wording, canonical_experience):
            failed_checks.append("publications_mismatch: 声明中的出版物信息与标准化经历不匹配")
            valid = False

        return valid

    def _validate_professional_context(
        self,
        wording: str,
        canonical_experience: Dict[str, Any],
        failed_checks: List[str]
    ) -> bool:
        """验证专业语境层级。"""
        # 专业语境应该基于确认的事实，但可以包含标准流程说明
        # 不应该包含未确认的具体细节

        # 检查是否包含合理的专业语境
        has_valid_context = False

        # 检查研究背景引用
        background = canonical_experience.get("background")
        if background and background in wording:
            has_valid_context = True

        # 检查问题目标引用
        problem_goal = canonical_experience.get("problem_or_goal")
        if problem_goal and problem_goal in wording:
            has_valid_context = True

        # 检查标准流程引用
        methods = canonical_experience.get("methods", [])
        if any(method in ["systematic_review", "meta_analysis"] for method in methods):
            if any(term in wording for term in ["PRISMA", "Cochrane", "异质性", "敏感性"]):
                has_valid_context = True

        # 如果没有有效的专业语境，也不一定是错误（可能是其他类型声明）
        return True

    def _validate_role_value(
        self,
        wording: str,
        target_role: str,
        failed_checks: List[str]
    ) -> bool:
        """验证岗位价值层级。"""
        # 岗位价值表达是允许的，甚至是鼓励的
        # 检查是否包含适当的岗位价值语言

        value_expressions_found = []
        for category, patterns in self.role_value_patterns.items():
            for pattern in patterns:
                if pattern in wording:
                    value_expressions_found.append(pattern)
                    break

        # 找到价值表达是好的，不是错误
        return True

    def _validate_future_interests(
        self,
        wording: str,
        failed_checks: List[str]
    ) -> bool:
        """验证未来兴趣层级。"""
        # 检查是否明确标识为未来方向
        has_future_indicators = any(re.search(pattern, wording) for pattern in self.future_interest_indicators)

        # 如果包含未来兴趣但没有标识，可能需要澄清
        # 但这通常不是硬性错误，除非与硬事实冲突

        return True

    def _extract_hard_facts_from_canonical(self, canonical_experience: Dict[str, Any]) -> Set[str]:
        """从标准化经历中提取硬事实集合。"""
        hard_facts = set()

        # 教育和背景信息
        context = canonical_experience.get("context", {})
        if context.get("topic"):
            hard_facts.add(context["topic"])

        # 责任信息
        role = canonical_experience.get("role", {})
        if role.get("responsibility_level"):
            hard_facts.add(role["responsibility_level"])

        # 数字范围
        scope = canonical_experience.get("scope", {})
        for key, value in scope.items():
            hard_facts.add(f"{key}:{value}")

        # 工具和方法
        tools = canonical_experience.get("tools", [])
        methods = canonical_experience.get("methods", [])
        hard_facts.update(tools)
        hard_facts.update(methods)

        # 出版物信息
        outcomes = canonical_experience.get("outcomes", [])
        hard_facts.update(outcomes)

        return hard_facts

    def _validate_numbers_consistency(self, wording: str, canonical_experience: Dict[str, Any]) -> bool:
        """验证数字一致性。"""
        # 提取声明中的数字
        wording_numbers = re.findall(r'\d+', wording)
        if not wording_numbers:
            return True

        # 提取标准化经历中的数字
        scope = canonical_experience.get("scope", {})
        scope_numbers = []
        for value in scope.values():
            if isinstance(value, str):
                scope_numbers.extend(re.findall(r'\d+', value))

        # 检查所有声明中的数字是否在标准化经历中
        for num in wording_numbers:
            if num not in scope_numbers:
                return False

        return True

    def _validate_responsibility_consistency(
        self,
        wording: str,
        responsibility_level: str,
        canonical_experience: Dict[str, Any]
    ) -> bool:
        """验证责任级别一致性。"""
        # 明确的责任升级指标。这里的 level 来自 canonical record。
        responsibility_upgrade_indicators = {
            "participated": [
                r"独立完成", r"独立负责", r"独立主导", r"牵头", r"主导",
                r"核心负责", r"全程负责", r"负责", r"管理", r"领导",
                r"\blead\b", r"\bled\b", r"\bleading\b", r"\bowner\b",
                r"\bmanag(?:e|ed|ing)\b", r"\bindependently\s+completed\b",
            ],
            "owned_component": [
                r"独立主导", r"牵头", r"主导", r"管理", r"领导",
                r"overall responsibility", r"\blead\b", r"\bled\b", r"\bleading\b", r"\bowner\b",
            ],
            "led_delivery": ["管理", "overall responsibility"],
            "project_owner": []
        }

        # 检查当前责任级别是否包含升级指标
        if responsibility_level in responsibility_upgrade_indicators:
            upgrade_indicators = responsibility_upgrade_indicators[responsibility_level]
            for indicator in upgrade_indicators:
                if re.search(indicator, wording, flags=re.IGNORECASE):
                    return False

        # owned_component 只允许对用户明确确认的具体模块使用“独立”。
        if responsibility_level == "owned_component" and re.search(
            r"独立(?:完成|负责)|\bindependently\s+completed\b", wording, flags=re.IGNORECASE
        ):
            boundary = str(canonical_experience.get("role", {}).get("personal_boundary") or "")
            if not boundary or not re.search(r"独立(?:完成|负责)|independently", boundary, flags=re.IGNORECASE):
                return False
            module_terms = (
                "文献检索", "文献筛选", "筛选", "数据提取", "统计分析", "数据分析",
                "实验", "问卷", "随访", "写作", "可视化", "数据库", "模块",
            )
            wording_modules = {term for term in module_terms if term in wording}
            boundary_modules = {term for term in module_terms if term in boundary}
            if not wording_modules or not wording_modules.intersection(boundary_modules):
                return False

        return True

    def _validate_tools_methods_consistency(
        self,
        wording: str,
        canonical_experience: Dict[str, Any]
    ) -> bool:
        """验证工具和方法一致性。"""
        canonical_tools = set(canonical_experience.get("tools", []))
        canonical_methods = set(canonical_experience.get("methods", []))
        canonical_actions = set(canonical_experience.get("actions", []))

        # 检查声明中提到的工具是否在标准化经历中
        tool_patterns = {
            "SPSS": "spss",
            "R": "r",
            "EndNote": "endnote",
            "NoteExpress": "noteexpress",
            "Python": "python",
            "Stata": "stata",
            "SAS": "sas"
        }
        for pattern, canonical_tool in tool_patterns.items():
            if pattern in wording and canonical_tool not in canonical_tools:
                return False

        # 检查声明中提到的方法是否在标准化经历中
        method_patterns = {
            "系统综述": "systematic_review",
            "Meta分析": "meta_analysis",
            "流行病学调查": "epidemiological_survey",
            "队列研究": "cohort_study",
            "病例对照": "case_control"
        }
        for pattern, canonical_method in method_patterns.items():
            if pattern in wording and canonical_method not in canonical_methods:
                return False

        # 检查声明中提到的动作是否在标准化经历中
        action_patterns = {
            "文献检索": "retrieve_literature",
            "筛选": "screen_studies",
            "数据提取": "extract_data",
            "统计分析": "analyze_data",
            "实验操作": "perform_experiments"
        }
        for pattern, canonical_action in action_patterns.items():
            if pattern in wording and canonical_action not in canonical_actions:
                return False

        return True

    def _validate_publications_consistency(
        self,
        wording: str,
        canonical_experience: Dict[str, Any]
    ) -> bool:
        """验证出版物一致性。"""
        canonical_outcomes = set(canonical_experience.get("outcomes", []))

        # 检查声明中提到的具体署名位置
        if "第一作者" in wording:
            # 检查标准化经历中是否包含第一作者信息
            if not any("第一作者" in outcome for outcome in canonical_outcomes):
                return False
        elif "第二作者" in wording:
            if not any("第二作者" in outcome for outcome in canonical_outcomes):
                return False
        elif "第三作者" in wording:
            if not any("第三作者" in outcome for outcome in canonical_outcomes):
                return False

        # 检查其他出版物信息
        publication_patterns = ["在投", "发表", "论文", "manuscript"]
        for pattern in publication_patterns:
            if pattern in wording:
                # 如果提到了出版物相关词汇，应该在outcomes中有对应信息
                if not any(pattern in outcome for outcome in canonical_outcomes):
                    return False

        return True


# 示例用法
if __name__ == "__main__":
    # 测试语义分层Claim Gate
    service = SemanticClaimGateService()

    # V3.2样例声明
    v32_claim = {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_v32_001",
        "experience_id": "v32_meta_analysis_001",
        "role_pack": "doctoral_v1",
        "wording": "系统参与Meta分析完整流程，独立完成文献检索、筛选和数据提取，并参与统计分析与结果解释",
        "used_facts": ["actions:retrieve_literature", "actions:screen_studies", "actions:extract_data"],
        "evidence_ids": ["ev_v32_001"],
        "responsibility_level": "participated",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "candidate",
        "user_disposition": None
    }

    # V3.2标准化经历
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

    print("语义分层Claim Gate结果:")
    print(f"状态: {result.status}")
    print(f"硬事实有效: {result.hard_facts_valid}")
    print(f"专业语境有效: {result.professional_context_valid}")
    print(f"岗位价值有效: {result.role_value_valid}")
    print(f"未来兴趣有效: {result.future_interests_valid}")
    print(f"失败检查: {result.failed_checks}")
    print(f"风险标志: {result.risk_flags}")
