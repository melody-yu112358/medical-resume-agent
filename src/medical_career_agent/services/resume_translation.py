from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CapabilityRecommendation:
    capability: str
    evidence_ids: tuple[str, ...]
    placement: str
    market_value: str
    rationale: str


@dataclass(frozen=True)
class ResumeTranslationResult:
    target_profile: str
    target_label: str
    recommendations: tuple[CapabilityRecommendation, ...]
    gaps: tuple[str, ...]
    version: str = "resume-translation-v0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TARGET_PROFILES = {
    "doctoral": {
        "label": "考博 / 保研",
        "priority": ("research_method", "data_analysis", "wet_lab", "clinical_research", "medical_information"),
        "translations": {
            "research_method": ("因果推断与循证研究方法", "核心能力 + 科研经历首条"),
            "data_analysis": ("研究数据处理与统计分析", "方法与技能 + 科研经历首条"),
            "wet_lab": ("实验技术与机制研究执行", "实验技术 + 科研经历首条"),
            "clinical_research": ("临床研究设计与证据转化", "科研经历首条"),
            "medical_information": ("系统检索与证据综合", "科研方法 + 文献成果"),
        },
    },
    "clinical_research": {
        "label": "临床科研岗",
        "priority": ("clinical_research", "research_method", "data_analysis", "medical_information", "wet_lab"),
        "translations": {
            "research_method": ("研究设计与循证分析", "核心能力 + 科研经历首条"),
            "data_analysis": ("临床数据分析与结果解释", "核心能力 + 科研经历首条"),
            "wet_lab": ("实验执行与质量控制", "实验技术栏目"),
            "clinical_research": ("临床研究执行与研究设计理解", "相关经历首条"),
            "medical_information": ("临床证据检索与综合", "核心能力 + 科研经历"),
        },
    },
    "medical_affairs": {
        "label": "MSL / 医学事务",
        "priority": ("medical_information", "clinical_research", "research_method", "data_analysis", "wet_lab"),
        "translations": {
            "research_method": ("研究证据解读能力", "核心能力 + 研究成果"),
            "data_analysis": ("医学数据结果解读", "核心能力 + 项目经历"),
            "wet_lab": ("疾病机制与实验背景", "专业背景 / 项目经历"),
            "clinical_research": ("临床研究理解与医学沟通基础", "相关经历首条"),
            "medical_information": ("医学信息检索与证据转译", "核心能力 + 项目经历首条"),
        },
    },
    "health_data": {
        "label": "医疗数据 / 健康科技",
        "priority": ("data_analysis", "research_method", "clinical_research", "medical_information", "wet_lab"),
        "translations": {
            "research_method": ("因果推断与分析框架", "核心能力 + 项目经历首条"),
            "data_analysis": ("医疗数据处理与统计建模", "核心能力 + 项目经历首条"),
            "wet_lab": ("医学问题与机制理解", "专业背景"),
            "clinical_research": ("临床数据与研究场景理解", "项目经历"),
            "medical_information": ("医学证据与需求转译", "项目经历 + 核心能力"),
        },
    },
}


class ResumeTranslationService:
    """Maps confirmed medical capabilities to a target JD without inventing facts."""

    def translate(
        self, *, resume_document: dict[str, Any], jd_text: str,
        target_profile: str = "clinical_research",
    ) -> ResumeTranslationResult:
        if resume_document.get("schema_version") != "resume-document-v1":
            raise ValueError("resume_document must use resume-document-v1")
        if not jd_text.strip():
            raise ValueError("jd_text cannot be empty")
        if target_profile not in TARGET_PROFILES:
            raise ValueError("target_profile is not supported")

        confirmed_evidence = {
            item["evidence_id"]
            for item in resume_document.get("evidence", [])
            if item.get("status") == "user_confirmed"
        }
        capabilities = tuple(resume_document.get("capability_profile", []))
        recommendations = []
        for capability in capabilities:
            evidence_ids = tuple(capability.get("evidence_ids", []))
            if not evidence_ids or not set(evidence_ids).issubset(confirmed_evidence):
                continue
            market_value, placement = TARGET_PROFILES[target_profile]["translations"].get(
                capability.get("category"), ("可核实的医学专业能力", "核心能力")
            )
            recommendations.append(
                CapabilityRecommendation(
                    capability=str(capability.get("name", "")),
                    evidence_ids=evidence_ids,
                    placement=placement,
                    market_value=market_value,
                    rationale=(
                        f"该能力由 {len(evidence_ids)} 条用户确认原文支持；"
                        "建议按目标岗位需求决定是否前置，不能据此扩写职责或成果。"
                    ),
                )
            )
        recommendations.sort(key=lambda item: self._priority(item, jd_text, target_profile), reverse=True)
        gaps = () if recommendations else (
            "尚未确认可直接翻译为岗位能力的医学方法、技术或工具；请先确认能力画像。",
        )
        return ResumeTranslationResult(
            target_profile, TARGET_PROFILES[target_profile]["label"], tuple(recommendations), gaps
        )

    @staticmethod
    def _priority(item: CapabilityRecommendation, jd_text: str, target_profile: str) -> int:
        text = jd_text.lower()
        keywords = {
            "研究方法与证据推理": ("科研", "研究", "博士", "phd", "统计", "证据"),
            "医学数据分析与结果解释": ("数据", "统计", "分析", "python", "r语言"),
            "实验技术与实验执行": ("实验", "分子", "细胞", "lab"),
            "临床研究执行与研究设计理解": ("临床", "队列", "研究", "gcp"),
            "医学证据检索与转译": ("医学事务", "msl", "文献", "证据", "沟通"),
        }
        category_priority = TARGET_PROFILES[target_profile]["priority"].index(
            next((category for category, value in TARGET_PROFILES[target_profile]["translations"].items() if value[0] == item.market_value), "medical_information")
        )
        return 10 - category_priority + sum(word in text for word in keywords.get(item.market_value, ()))
