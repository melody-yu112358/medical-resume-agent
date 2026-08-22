from __future__ import annotations

from dataclasses import dataclass, replace

from ..domain.career_models import (
    CapabilityCoverage,
    CareerHypothesis,
    CareerRecord,
    ConstraintFinding,
    MarketClaim,
    MedicalProfile,
    SupportingEvidence,
)


SCORING_VERSION = "career-comparison-v0.1"


@dataclass(frozen=True)
class _CapabilityGroup:
    group_id: str
    label: str
    profile_terms: tuple[str, ...]
    market_terms: tuple[str, ...]
    minimum_distinct_terms: int = 1


@dataclass(frozen=True)
class _CareerRule:
    group_weights: tuple[tuple[str, int], ...]
    anchor_groups: tuple[str, ...]
    unknown_keywords: tuple[str, ...]


CAPABILITY_GROUPS = {
    item.group_id: item
    for item in (
        _CapabilityGroup(
            "evidence_interpretation",
            "医学与研究证据解读",
            (
                "临床证据解读",
                "文献检索",
                "证据比较",
                "证据核对",
                "不确定性表达",
            ),
            ("文献", "证据", "临床数据", "科学论证"),
        ),
        _CapabilityGroup(
            "communication",
            "受众沟通与协作",
            (
                "口头表达",
                "回应问题",
                "受众适配",
                "跨专业沟通",
                "跨职能沟通",
                "跨角色沟通",
            ),
            ("沟通", "演讲", "讨论", "培训", "跨职能"),
        ),
        _CapabilityGroup(
            "project_coordination",
            "项目协调与推进",
            (
                "项目协调",
                "进度跟踪",
                "反馈迭代",
                "跨职能沟通",
                "跨角色沟通",
            ),
            ("项目", "推进", "时间管理", "组织协调", "跨职能"),
        ),
        _CapabilityGroup(
            "product_discovery",
            "用户问题与产品探索",
            ("用户访谈", "需求拆解", "原型制作", "问题定义"),
            ("需求", "产品设计", "原型", "需求文档"),
            minimum_distinct_terms=2,
        ),
        _CapabilityGroup(
            "data_analysis",
            "数据处理与分析",
            ("数据处理", "可复现工作"),
            ("数据分析", "产品评估", "决策"),
        ),
        _CapabilityGroup(
            "quality_documentation",
            "文件质量与可追溯性",
            (
                "规则记录",
                "数据核对",
                "文件追踪",
                "SOP执行",
                "事实与推断区分",
                "质量复盘",
                "证据核对",
            ),
            ("文件", "质量", "核对", "审阅", "可追溯", "审计"),
            minimum_distinct_terms=2,
        ),
        _CapabilityGroup(
            "clinical_research_operations",
            "临床研究运营",
            ("数据核对", "文件追踪", "问题升级", "项目协调", "进度跟踪"),
            ("GCP", "试验方案", "研究中心", "监查", "原始数据"),
            minimum_distinct_terms=2,
        ),
        _CapabilityGroup(
            "safety_case_processing",
            "药物安全信息处理",
            ("安全信息整理", "SOP执行", "医学判断边界识别"),
            ("GVP", "安全", "风险管理", "安全数据库", "报告"),
            minimum_distinct_terms=2,
        ),
        _CapabilityGroup(
            "compliance_boundary",
            "合规边界与风险识别",
            (
                "规则记录",
                "风险识别",
                "医学判断边界识别",
                "SOP执行",
                "事实与推断区分",
            ),
            ("法规", "合规", "SOP", "监管", "审计"),
        ),
        _CapabilityGroup(
            "medical_writing",
            "医学与结构化写作",
            ("医学写作", "结构化写作", "受众适配", "事实与推断区分"),
            ("写作", "文档", "文件", "呈现", "论证"),
        ),
    )
}


CAREER_RULES = {
    "medical-science-liaison": _CareerRule(
        group_weights=(
            ("evidence_interpretation", 3),
            ("communication", 3),
            ("project_coordination", 1),
            ("compliance_boundary", 1),
        ),
        anchor_groups=("evidence_interpretation", "communication"),
        unknown_keywords=("药企", "医学事务", "合规", "专家", "出差", "英文"),
    ),
    "clinical-research-associate": _CareerRule(
        group_weights=(
            ("clinical_research_operations", 3),
            ("quality_documentation", 2),
            ("project_coordination", 2),
            ("compliance_boundary", 1),
            ("evidence_interpretation", 1),
        ),
        anchor_groups=(
            "clinical_research_operations",
            "quality_documentation",
            "evidence_interpretation",
        ),
        unknown_keywords=("GCP", "监查", "临床试验", "研究中心", "出差", "英文"),
    ),
    "pharmacovigilance-specialist": _CareerRule(
        group_weights=(
            ("safety_case_processing", 3),
            ("quality_documentation", 2),
            ("compliance_boundary", 2),
            ("medical_writing", 1),
        ),
        anchor_groups=(
            "safety_case_processing",
            "quality_documentation",
            "compliance_boundary",
        ),
        unknown_keywords=("不良事件", "安全报告", "法规", "数据库", "英文", "监管"),
    ),
    "medical-writer": _CareerRule(
        group_weights=(
            ("medical_writing", 3),
            ("evidence_interpretation", 2),
            ("quality_documentation", 2),
            ("project_coordination", 1),
        ),
        anchor_groups=("medical_writing", "evidence_interpretation"),
        unknown_keywords=("写作", "英文", "审阅", "文件", "注册"),
    ),
    "healthcare-ai-product-manager": _CareerRule(
        group_weights=(
            ("product_discovery", 3),
            ("project_coordination", 2),
            ("communication", 2),
            ("data_analysis", 1),
            ("compliance_boundary", 1),
        ),
        anchor_groups=("product_discovery",),
        unknown_keywords=("产品", "算法", "医疗软件", "隐私", "采购", "原型", "市场"),
    ),
}


class CareerComparator:
    """Deterministic evidence coverage and constraint comparison.

    The percentage is evidence coverage for explicit capability groups. It is
    not a suitability, personality, employability, or success score.
    """

    def compare(
        self,
        profile: MedicalProfile,
        careers: list[CareerRecord],
        *,
        maximum_hypotheses: int = 3,
    ) -> tuple[tuple[CareerHypothesis, ...], tuple[ConstraintFinding, ...]]:
        if not 1 <= maximum_hypotheses <= 3:
            raise ValueError("maximum_hypotheses must be between 1 and 3")

        hypotheses: list[CareerHypothesis] = []
        all_findings: list[ConstraintFinding] = []
        for career in careers:
            rule = CAREER_RULES.get(career.career_id)
            if rule is None:
                continue

            components = tuple(
                self._coverage_component(profile, career, group_id, weight)
                for group_id, weight in rule.group_weights
            )
            if not any(
                component.matched and component.group_id in rule.anchor_groups
                for component in components
            ):
                continue

            total_weight = sum(component.weight for component in components)
            matched_weight = sum(
                component.weight for component in components if component.matched
            )
            raw_coverage = round(100 * matched_weight / total_weight)
            if raw_coverage < 25:
                continue

            findings = self._constraint_findings(profile, career)
            all_findings.extend(findings)
            penalty = sum(item.penalty_points for item in findings)
            adjusted_coverage = max(0, raw_coverage - penalty)
            hypotheses.append(
                CareerHypothesis(
                    career_id=career.career_id,
                    career_name=career.name,
                    rank=0,
                    evidence_coverage_percent=adjusted_coverage,
                    raw_evidence_coverage_percent=raw_coverage,
                    scoring_version=SCORING_VERSION,
                    components=components,
                    supporting_evidence=self._supporting_evidence(profile, components),
                    counter_evidence=self._counter_evidence(career),
                    gaps=tuple(
                        f"当前画像尚无能证明“{component.label}”的经历证据"
                        for component in components
                        if not component.matched
                    ),
                    unknowns=self._unknowns(profile, career, rule),
                    constraint_findings=findings,
                    validation_action=(
                        career.validation_actions[0]
                        if career.validation_actions
                        else "该职业卡尚未提供验证行动"
                    ),
                    career_review_status=career.review_status,
                )
            )

        ordered = sorted(
            hypotheses,
            key=lambda item: (
                -item.evidence_coverage_percent,
                -item.raw_evidence_coverage_percent,
                item.career_id,
            ),
        )[:maximum_hypotheses]
        ranked = tuple(replace(item, rank=index) for index, item in enumerate(ordered, 1))
        return ranked, tuple(all_findings)

    def _coverage_component(
        self,
        profile: MedicalProfile,
        career: CareerRecord,
        group_id: str,
        weight: int,
    ) -> CapabilityCoverage:
        group = CAPABILITY_GROUPS[group_id]
        matching_evidence = tuple(
            item
            for item in profile.evidence
            if set(item.capabilities).intersection(group.profile_terms)
        )
        distinct_terms = {
            capability
            for item in matching_evidence
            for capability in item.capabilities
            if capability in group.profile_terms
        }
        matched = len(distinct_terms) >= group.minimum_distinct_terms
        evidence_ids = (
            tuple(item.evidence_id for item in matching_evidence) if matched else ()
        )
        return CapabilityCoverage(
            group_id=group.group_id,
            label=group.label,
            weight=weight,
            matched=matched,
            evidence_ids=evidence_ids,
            career_source_ids=self._career_source_ids(career, group),
        )

    def _career_source_ids(
        self, career: CareerRecord, group: _CapabilityGroup
    ) -> tuple[str, ...]:
        source_ids = {
            source_id
            for claim in career.required_skills
            if any(term.lower() in claim.claim.lower() for term in group.market_terms)
            for source_id in claim.source_ids
        }
        if not source_ids:
            source_ids = {
                source_id
                for claim in career.required_skills
                for source_id in claim.source_ids
            }
        return tuple(sorted(source_ids))

    def _supporting_evidence(
        self,
        profile: MedicalProfile,
        components: tuple[CapabilityCoverage, ...],
    ) -> tuple[SupportingEvidence, ...]:
        groups_by_evidence: dict[str, list[str]] = {}
        for component in components:
            if component.matched:
                for evidence_id in component.evidence_ids:
                    groups_by_evidence.setdefault(evidence_id, []).append(component.label)

        evidence_by_id = {item.evidence_id: item for item in profile.evidence}
        return tuple(
            SupportingEvidence(
                evidence_id=evidence_id,
                statement=evidence_by_id[evidence_id].statement,
                capability_groups=tuple(groups_by_evidence[evidence_id]),
            )
            for evidence_id in evidence_by_id
            if evidence_id in groups_by_evidence
        )

    def _counter_evidence(self, career: CareerRecord) -> tuple[MarketClaim, ...]:
        negative_markers = ("不能", "不等于", "不能自动")
        items = [
            claim
            for claim in career.medical_transferable_skills
            if any(marker in claim.claim for marker in negative_markers)
        ]
        if career.entry_barriers:
            items.append(career.entry_barriers[0])

        unique: list[MarketClaim] = []
        seen: set[str] = set()
        for item in items:
            if item.claim not in seen:
                seen.add(item.claim)
                unique.append(item)
        return tuple(unique[:2])

    def _unknowns(
        self,
        profile: MedicalProfile,
        career: CareerRecord,
        rule: _CareerRule,
    ) -> tuple[str, ...]:
        unknowns = [
            item
            for item in profile.unknowns
            if any(keyword.lower() in item.lower() for keyword in rule.unknown_keywords)
        ]
        if profile.constraints.locations:
            locations = "、".join(profile.constraints.locations)
            unknowns.append(
                f"职业卡不是实时招聘列表，尚需确认{locations}当前是否有该方向岗位"
            )
        if career.review_status == "draft":
            unknowns.append("该职业卡仍为 draft，市场结论需要人工复核")
        return tuple(dict.fromkeys(unknowns))

    def _constraint_findings(
        self, profile: MedicalProfile, career: CareerRecord
    ) -> tuple[ConstraintFinding, ...]:
        travel_constraint = next(
            (
                item
                for item in profile.constraints.non_negotiables
                if "不接受" in item and "出差" in item
            ),
            None,
        )
        if travel_constraint is None:
            return ()

        source_ids = tuple(
            sorted(
                {
                    source_id
                    for claim in career.work_environment
                    for source_id in claim.source_ids
                }
            )
        )
        if career.career_id == "clinical-research-associate":
            return (
                ConstraintFinding(
                    career_id=career.career_id,
                    constraint=travel_constraint,
                    status="potential_conflict",
                    explanation=(
                        "职业卡显示工作通常需要现场访视；卡片没有给出统一频率，"
                        "因此先降级并要求按具体岗位核对，不能直接判定兼容。"
                    ),
                    penalty_points=25,
                    career_source_ids=source_ids,
                ),
            )
        if career.career_id == "medical-science-liaison":
            return (
                ConstraintFinding(
                    career_id=career.career_id,
                    constraint=travel_constraint,
                    status="needs_role_check",
                    explanation=(
                        "职业卡显示岗位包含区域拜访或现场交流，但出差强度因公司和"
                        "区域而异，因此先降级并保留为待核对假设。"
                    ),
                    penalty_points=15,
                    career_source_ids=source_ids,
                ),
            )
        return ()
