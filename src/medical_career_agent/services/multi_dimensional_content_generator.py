from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .bullet_composer import BulletClaim


@dataclass(frozen=True)
class ContentGenerationResult:
    """多维内容生成的结果，包含多个要点声明。"""

    experience_id: str
    target_role: str
    expression_tier: str  # "conservative", "professional", "high_impact"
    bullet_claims: List[BulletClaim]
    generation_metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "target_role": self.target_role,
            "expression_tier": self.expression_tier,
            "bullet_claims": [claim.to_dict() for claim in self.bullet_claims],
            "generation_metadata": self.generation_metadata
        }


# ---------------------------------------------------------------------------
# 枚举 -> 自然中文医学表达 映射层
# ---------------------------------------------------------------------------
TERM_MAP = {
    # 动作
    "retrieve_literature": "文献检索",
    "screen_studies": "研究筛选",
    "extract_data": "结构化数据提取",
    "analyze_data": "数据分析",
    "design_study": "研究设计",
    "implement_protocol": "方案实施",
    "perform_experiments": "实验操作",
    "collect_samples": "样本收集",
    "write_manuscript": "论文撰写",
    "collect_patient_history": "病史采集",
    "perform_physical_exam": "体格检查",
    "interpret_auxiliary_exams": "辅助检查解读",
    "participate_in_case_discussions": "病例讨论参与",
    "design_questionnaire": "问卷设计",
    "collect_data": "数据收集",
    "interpret_results": "结果解释",
    "write_medical_records": "病历书写",
    # 对象
    "medical_literature": "医学文献",
    "clinical_studies": "临床研究",
    "clinical_data": "临床数据",
    "research_outcomes": "研究结果",
    "cell_samples": "细胞样本",
    "protein_extracts": "蛋白提取物",
    "patient_records": "患者记录",
    "survey_responses": "调查问卷",
    "medical_student_cohort": "医学生队列",
    "cardiology_patients": "心脏病患者",
    "clinical_cases": "临床病例",
    # 方法
    "systematic_review": "系统综述",
    "meta_analysis": "Meta分析",
    "statistical_analysis": "统计分析",
    "regression_modeling": "回归建模",
    "pcr": "PCR",
    "western_blot": "Western Blot",
    "qPCR": "qPCR",
    "cell_culture": "细胞培养",
    "cohort_study": "队列研究",
    "cross_sectional_survey": "横断面调查",
    "descriptive_statistics": "描述性统计",
    "logistic_regression": "Logistic回归",
    "clinical_assessment": "临床评估",
    "differential_diagnosis": "鉴别诊断",
    "treatment_planning": "治疗方案制定",
    # 工具
    "spss": "SPSS",
    "SPSS": "SPSS",
    "r": "R",
    "R": "R",
    "sas": "SAS",
    "stata": "Stata",
    "python": "Python",
    "excel": "Excel",
    "Excel": "Excel",
    "endnote": "EndNote",
    "EndNote": "EndNote",
    "noteexpress": "NoteExpress",
    "NoteExpress": "NoteExpress",
    "pubmed": "PubMed",
    "PubMed": "PubMed",
    "embase": "Embase",
    "Embase": "Embase",
    "cochrane": "Cochrane",
    "Cochrane": "Cochrane",
    "dual_screening": "双重筛选",
    "prisma_compliance": "PRISMA合规",
    "cochrane_rob": "Cochrane偏倚风险评估",
    "standardized_forms": "标准化表格",
}

STAT_TOOLS = {"r", "spss", "sas", "stata", "python"}
DATABASE_TOOLS = {"pubmed", "embase", "cochrane", "medline", "web of science"}


def cn(item: Any) -> str:
    """枚举 -> 中文医学表达；原文已是中文则原样返回。"""
    if not isinstance(item, str):
        return str(item)
    return TERM_MAP.get(item, item)


def has_text(exp: Dict[str, Any], *fields: str) -> bool:
    for field in fields:
        value = exp.get(field)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, (list, tuple)) and any(str(v).strip() for v in value):
            return True
        if isinstance(value, dict) and value:
            return True
    return False


def to_list(exp: Dict[str, Any], field: str) -> List[str]:
    value = exp.get(field, [])
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return []


def join_items(exp: Dict[str, Any], field: str, sep: str = "、") -> str:
    return sep.join(to_list(exp, field))


def scope_value(exp: Dict[str, Any], key: str, default: str = "") -> str:
    scope = exp.get("scope", {}) or {}
    value = scope.get(key, "")
    return str(value) if value else default


def contains_any(exp: Dict[str, Any], fields: List[str], *terms: str) -> bool:
    for field in fields:
        for item in to_list(exp, field):
            text = str(item)
            if any(t in text for t in terms):
                return True
    return False


def pick_hits(exp: Dict[str, Any], fields: List[str], *terms: str) -> List[str]:
    hits = []
    for field in fields:
        for item in to_list(exp, field):
            if any(t in str(item) for t in terms):
                hits.append(str(item))
    return hits


def role_category(target_role: str) -> str:
    if target_role.startswith("doctoral"):
        return "doctoral"
    if target_role.startswith("clinical_research"):
        return "clinical_research"
    if target_role.startswith("medical_affairs"):
        return "medical_affairs"
    if target_role.startswith("health_ai_data"):
        return "health_ai_data"
    return "doctoral"


ROLE_VALUE_TEXT = {
    "doctoral": {
        "research_question": "体现科学问题识别能力",
        "pico_framework": "体现研究方法学严谨性",
        "database_retrieval": "体现系统性文献检索能力",
        "study_screening": "体现证据筛选与质控意识",
        "inclusion_exclusion": "体现纳入标准制定严谨性",
        "bias_assessment": "体现证据批判性评价能力",
        "data_extraction": "体现结构化数据处理能力",
        "statistical_analysis": "体现统计方法与结果解释能力",
        "heterogeneity_interpretation": "体现统计判断与临床洞察",
        "result_interpretation": "体现结果解释与循证思维",
        "manuscript_contribution": "体现学术写作与论文贡献",
        "academic_presentation": "体现科研汇报与沟通能力",
        "collaboration": "体现团队协作与科研执行",
        "methodology_insight": "体现方法学理解与科研素养",
        "research_workflow": "体现科研流程执行能力",
        "questionnaire_design": "体现调查工具设计能力",
        "data_collection": "体现数据采集与质量管理",
        "quality_control": "体现数据质量控制能力",
        "results_application": "体现研究结果转化与建议能力",
        "project_report": "体现学术汇报与成果展示能力",
        "clinical_domain": "体现专科临床思维",
        "medical_history_exam": "体现病史采集与体格检查规范",
        "ward_rounds": "体现病历书写与查房参与",
        "auxiliary_exams": "体现辅助检查解读与整合",
        "clinical_operations": "体现基础临床操作技能",
        "clinical_reasoning": "体现临床推理与鉴别诊断",
        "clinical_communication": "体现医患沟通与协作",
        "research_awareness": "体现科研问题识别意识",
        "experiment_operation": "体现实验操作规范性",
        "quality_control_lab": "体现实验质控意识",
        "data_recording": "体现数据记录与可追溯性",
        "result_interpretation_lab": "体现实验结果解读能力",
    },
    "clinical_research": {
        "research_question": "体现临床问题转化为研究问题的能力",
        "database_retrieval": "体现系统性检索执行能力",
        "study_screening": "体现研究筛选与数据质量意识",
        "bias_assessment": "体现证据质量评价能力",
        "data_extraction": "体现临床研究数据管理能力",
        "statistical_analysis": "体现临床研究统计分析能力",
        "result_interpretation": "体现临床结果解读能力",
        "collaboration": "体现临床研究团队协作能力",
        "research_workflow": "体现临床研究流程执行能力",
        "clinical_domain": "体现临床背景理解能力",
        "ward_rounds": "体现临床研究所需的临床能力",
        "clinical_operations": "体现临床操作规范性",
    },
    "medical_affairs": {
        "research_question": "体现治疗领域临床问题理解",
        "database_retrieval": "体现证据检索与整合能力",
        "bias_assessment": "体现证据分级与批判性评价",
        "data_extraction": "体现医学证据结构化整合能力",
        "statistical_analysis": "体现医学统计结果解读能力",
        "result_interpretation": "体现循证医学沟通能力",
        "manuscript_contribution": "体现医学写作与学术表达",
        "academic_presentation": "体现医学信息沟通能力",
        "methodology_insight": "体现医学证据方法学理解",
        "clinical_domain": "体现治疗领域临床知识",
    },
    "health_ai_data": {
        "database_retrieval": "体现系统化信息采集能力",
        "data_extraction": "体现结构化数据建模能力",
        "statistical_analysis": "体现数据分析与建模能力",
        "result_interpretation": "体现数据洞察与解释能力",
        "quality_control": "体现数据质量控制能力",
        "data_collection": "体现数据工程与采集能力",
        "research_workflow": "体现数据分析流程执行能力",
        "collaboration": "体现跨职能协作能力",
    },
}


def role_value_text(dimension: str, target_role: str) -> str:
    role = role_category(target_role)
    mapping = ROLE_VALUE_TEXT.get(role, {})
    return mapping.get(dimension, "体现相应科研与岗位价值")


# ---------------------------------------------------------------------------
# 维度规划：先确定"经历类型候选维度"，再按已确认事实门控
# ---------------------------------------------------------------------------
# Meta / 系统综述候选维度
EVIDENCE_SYNTHESIS_DIMS = [
    "research_question",
    "pico_framework",
    "search_strategy",
    "database_retrieval",
    "study_screening",
    "inclusion_exclusion",
    "bias_assessment",
    "data_extraction",
    "statistical_analysis",
    "heterogeneity_interpretation",
    "result_interpretation",
    "manuscript_contribution",
    "academic_presentation",
    "collaboration",
    "methodology_insight",
]

# 大创 / 流行病学候选维度
EPIDEMIOLOGY_DIMS = [
    "research_question",
    "questionnaire_design",
    "data_collection",
    "quality_control",
    "statistical_analysis",
    "results_application",
    "project_report",
    "collaboration",
]

# 临床候选维度
CLINICAL_DIMS = [
    "clinical_domain",
    "medical_history_exam",
    "ward_rounds",
    "auxiliary_exams",
    "clinical_operations",
    "clinical_reasoning",
    "clinical_communication",
    "research_awareness",
    "collaboration",
]

# 湿实验候选维度
WETLAB_DIMS = [
    "research_question",
    "experiment_operation",
    "quality_control_lab",
    "data_recording",
    "result_interpretation_lab",
    "collaboration",
    "methodology_insight",
]


def _gate_evidence_synthesis(exp: Dict[str, Any]) -> List[str]:
    """Meta/系统综述：只有事实已确认的维度才被选中。"""
    selected = []
    actions = set(exp.get("actions", []))
    methods = set(exp.get("methods", []))
    tools = set(exp.get("tools", []))
    lower_tools = {str(t).lower() for t in tools}

    # research_question
    if has_text(exp, "problem_or_goal", "background", "research_question"):
        selected.append("research_question")
    # pico_framework
    if contains_any(exp, ["workflow_steps", "pico_framework"], "PICO"):
        selected.append("pico_framework")
    # search_strategy
    if contains_any(exp, ["workflow_steps", "search_strategy"], "检索策略", "检索") or "search_strategy" in exp:
        selected.append("search_strategy")
    # database_retrieval：需要实际数据库证据（数据库工具/数据库数量/检索短语），
    # 仅"参与检索"不足以支撑"多数据库检索"
    if (
        bool(lower_tools & DATABASE_TOOLS)
        or has_text(exp, "databases_used", "database_retrieval")
        or scope_value(exp, "database_count")
        or contains_any(exp, ["workflow_steps"], "数据库", "多库", "多数据库")
    ):
        selected.append("database_retrieval")
    # study_screening
    if "screen_studies" in actions or contains_any(exp, ["quality_control", "workflow_steps"], "筛选"):
        selected.append("study_screening")
    # inclusion_exclusion
    if contains_any(exp, ["quality_control", "screening_criteria", "workflow_steps"], "纳入", "排除", "标准"):
        selected.append("inclusion_exclusion")
    # bias_assessment
    if (
        contains_any(exp, ["quality_control", "quality_assessment", "bias_assessment"], "偏倚", "RoB", "Cochrane")
        or "bias_assessment" in exp
        or scope_value(exp, "bias_assessment")
    ):
        selected.append("bias_assessment")
    # data_extraction
    if (
        "extract_data" in actions
        or has_text(exp, "data_extraction")
        or contains_any(exp, ["quality_control", "workflow_steps"], "提取", "表格", "结构化")
    ):
        selected.append("data_extraction")
    # statistical_analysis：需要明确的数据分析事实，
    # 仅确认"meta_analysis"方法不足以支撑"已完成统计分析"
    if (
        "analyze_data" in actions
        or bool(lower_tools & STAT_TOOLS)
        or has_text(exp, "statistical_analysis")
        or contains_any(exp, ["workflow_steps", "decisions_or_judgments"], "统计", "分析", "异质性", "敏感性")
    ):
        selected.append("statistical_analysis")
    # heterogeneity_interpretation
    if "meta_analysis" in methods and (
        bool(lower_tools & STAT_TOOLS) or contains_any(exp, ["decisions_or_judgments"], "异质性", "敏感性")
    ):
        selected.append("heterogeneity_interpretation")
    # result_interpretation
    if has_text(exp, "results_interpretation", "result_interpretation") or "interpret_results" in actions:
        selected.append("result_interpretation")
    # manuscript_contribution
    if any("作者" in o or "论文" in o or "在投" in o or "发表" in o or "投稿" in o for o in exp.get("outcomes", [])):
        selected.append("manuscript_contribution")
    # academic_presentation
    if contains_any(exp, ["outputs", "outcomes", "presentation"], "汇报", "组会", "展示", "presentation"):
        selected.append("academic_presentation")
    # collaboration
    if has_text(exp, "collaboration"):
        selected.append("collaboration")
    # methodology_insight
    if has_text(exp, "insights") or contains_any(exp, ["capability_evidence"], "方法学", "循证"):
        selected.append("methodology_insight")

    return selected


def _gate_epidemiology(exp: Dict[str, Any]) -> List[str]:
    selected = []
    actions = set(exp.get("actions", []))

    if has_text(exp, "problem_or_goal", "background", "research_question"):
        selected.append("research_question")
    if "design_questionnaire" in actions or contains_any(exp, ["workflow_steps", "questionnaire_design"], "问卷"):
        selected.append("questionnaire_design")
    if "collect_data" in actions or has_text(exp, "sample_size") or contains_any(exp, ["outputs"], "问卷"):
        selected.append("data_collection")
    if has_text(exp, "quality_control"):
        selected.append("quality_control")
    if (
        "analyze_data" in actions
        or any(m in exp.get("methods", []) for m in ["descriptive_statistics", "logistic_regression", "statistical_analysis"])
        or has_text(exp, "statistical_methods")
    ):
        selected.append("statistical_analysis")
    if has_text(exp, "key_findings", "recommendations", "results_application"):
        selected.append("results_application")
    if contains_any(exp, ["outcomes", "outputs", "artifacts"], "结题", "报告", "汇报", "答辩"):
        selected.append("project_report")
    if has_text(exp, "collaboration"):
        selected.append("collaboration")

    return selected


def _gate_clinical(exp: Dict[str, Any]) -> List[str]:
    selected = []
    actions = set(exp.get("actions", []))

    if scope_value(exp, "main_conditions") or has_text(exp, "main_conditions", "patient_cases"):
        selected.append("clinical_domain")
    if "collect_patient_history" in actions or "perform_physical_exam" in actions or contains_any(exp, ["clinical_skills"], "病史", "体格"):
        selected.append("medical_history_exam")
    if contains_any(exp, ["workflow_steps", "clinical_skills"], "查房", "病历", "方案讨论"):
        selected.append("ward_rounds")
    if "interpret_auxiliary_exams" in actions or contains_any(exp, ["auxiliary_exams", "tools"], "心电图", "超声", "影像", "实验室"):
        selected.append("auxiliary_exams")
    if contains_any(exp, ["basic_operations", "tools"], "采血", "心电图", "生命体征", "操作"):
        selected.append("clinical_operations")
    if contains_any(exp, ["decisions_or_judgments", "workflow_steps"], "鉴别", "方案制定", "诊断"):
        selected.append("clinical_reasoning")
    if contains_any(exp, ["workflow_steps", "clinical_skills"], "病例讨论", "健康教育", "沟通"):
        selected.append("clinical_communication")
    if has_text(exp, "research_inspiration", "research_awareness") or contains_any(exp, ["insights", "research_interest_link"], "循证", "科研", "问题"):
        selected.append("research_awareness")
    if has_text(exp, "collaboration"):
        selected.append("collaboration")

    return selected


def _gate_wetlab(exp: Dict[str, Any]) -> List[str]:
    selected = []
    actions = set(exp.get("actions", []))
    methods = set(exp.get("methods", []))

    if has_text(exp, "problem_or_goal", "background", "research_question"):
        selected.append("research_question")
    if "perform_experiments" in actions or methods & {"cell_culture", "qPCR", "pcr", "western_blot"}:
        selected.append("experiment_operation")
    if has_text(exp, "quality_control") or contains_any(exp, ["workflow_steps"], "对照", "复孔", "质控"):
        selected.append("quality_control_lab")
    if has_text(exp, "lab_records", "data_records") or contains_any(exp, ["workflow_steps"], "记录", "数据整理"):
        selected.append("data_recording")
    if has_text(exp, "outcomes", "outputs", "insights") or contains_any(exp, ["workflow_steps"], "结果", "分析"):
        selected.append("result_interpretation_lab")
    if has_text(exp, "collaboration"):
        selected.append("collaboration")
    if has_text(exp, "insights") or contains_any(exp, ["capability_evidence"], "方法学", "实验"):
        selected.append("methodology_insight")

    return selected


def plan_dimensions(exp: Dict[str, Any]) -> List[str]:
    """根据经历类型与已确认事实，动态选择适用维度。

    规则：
    - 先按 experience_type 或 context.domain 判定经历类型；
    - 再对每类候选维度逐个做"事实门控"——只有事实已确认才选中；
    - 不同经历可得到不同维度数量与组成。
    """
    context = exp.get("context", {})
    domain = context.get("domain", "clinical_research")
    experience_type = exp.get("experience_type", "")

    # 明确类型优先
    if "meta" in experience_type or "systematic" in experience_type:
        base = _gate_evidence_synthesis(exp)
    elif experience_type in ("wet_lab", "实验", "湿实验"):
        base = _gate_wetlab(exp)
    elif experience_type in ("clinical", "临床实习", "clinical_practice"):
        base = _gate_clinical(exp)
    elif experience_type in ("survey", "大创", "流行病学", "innovation"):
        base = _gate_epidemiology(exp)
    else:
        # 依据 domain 兜底
        if domain == "clinical_research":
            base = _gate_evidence_synthesis(exp)
        elif domain == "wet_lab":
            base = _gate_wetlab(exp)
        elif domain == "clinical_practice":
            base = _gate_clinical(exp)
        elif domain == "epidemiology_research":
            base = _gate_epidemiology(exp)
        else:
            base = _gate_evidence_synthesis(exp)

    # 去重保序
    seen = set()
    ordered = []
    for dim in base:
        if dim not in seen:
            seen.add(dim)
            ordered.append(dim)
    return ordered


def missing_dimensions(exp: Dict[str, Any], selected: List[str]) -> List[str]:
    """返回值得追问但当前事实不足的候选维度（供 Question Planner 补充）。"""
    context = exp.get("context", {})
    domain = context.get("domain", "clinical_research")
    experience_type = exp.get("experience_type", "")

    if "meta" in experience_type or "systematic" in experience_type or domain == "clinical_research":
        candidates = EVIDENCE_SYNTHESIS_DIMS
    elif experience_type in ("survey", "大创", "流行病学", "innovation") or domain == "epidemiology_research":
        candidates = EPIDEMIOLOGY_DIMS
    elif experience_type in ("clinical", "临床实习", "clinical_practice") or domain == "clinical_practice":
        candidates = CLINICAL_DIMS
    elif experience_type in ("wet_lab", "实验", "湿实验") or domain == "wet_lab":
        candidates = WETLAB_DIMS
    else:
        candidates = EVIDENCE_SYNTHESIS_DIMS

    selected_set = set(selected)
    return [c for c in candidates if c not in selected_set]


# ---------------------------------------------------------------------------
# 角色优先级（仅影响排序，不改变事实）
# ---------------------------------------------------------------------------
ROLE_PRIORITY = {
    "doctoral": [
        "research_question", "pico_framework", "search_strategy", "database_retrieval",
        "study_screening", "inclusion_exclusion", "bias_assessment", "data_extraction",
        "statistical_analysis", "heterogeneity_interpretation", "result_interpretation",
        "manuscript_contribution", "academic_presentation", "collaboration", "methodology_insight",
        # 临床/其他经历在博士目标下仍优先展示临床核心覆盖
        "clinical_domain", "ward_rounds", "auxiliary_exams", "clinical_operations",
        "medical_history_exam", "clinical_reasoning", "clinical_communication", "research_awareness",
        "questionnaire_design", "data_collection", "quality_control", "results_application", "project_report",
    ],
    "clinical_research": [
        "research_question", "clinical_domain", "database_retrieval", "study_screening",
        "data_extraction", "bias_assessment", "statistical_analysis", "clinical_operations",
        "ward_rounds", "medical_history_exam",
    ],
    "medical_affairs": [
        "research_question", "database_retrieval", "bias_assessment", "data_extraction",
        "result_interpretation", "manuscript_contribution", "academic_presentation",
        "methodology_insight", "clinical_domain",
    ],
    "health_ai_data": [
        "data_extraction", "data_collection", "statistical_analysis", "quality_control",
        "result_interpretation", "database_retrieval", "research_workflow",
    ],
}


def order_dimensions(selected: List[str], target_role: str, experience: Optional[Dict[str, Any]] = None) -> List[str]:
    """按经历类型与目标岗位排序。

    通用规则：
    - 临床/大创/湿实验经历优先展示其核心覆盖维度（不同经历产生不同结构）；
    - 其余维度按目标岗位优先级排序。
    """
    if experience is not None:
        context = experience.get("context", {})
        domain = context.get("domain", "")
        experience_type = experience.get("experience_type", "")

        # 大创/流行病学：问卷设计、数据收集、质量控制、统计分析、结果应用优先
        if experience_type in ("survey", "大创", "流行病学", "innovation") or domain == "epidemiology_research":
            coverage = [
                "questionnaire_design", "data_collection", "quality_control",
                "statistical_analysis", "results_application", "project_report",
            ]
            ordered = [d for d in coverage if d in selected]
            ordered.extend([d for d in selected if d not in ordered])
            return ordered

        # 临床实习：科室病种、病历查房、辅助检查、临床操作、科研意识/沟通优先
        if experience_type in ("clinical", "临床实习", "clinical_practice") or domain == "clinical_practice":
            coverage = [
                "clinical_domain", "medical_history_exam", "ward_rounds",
                "auxiliary_exams", "clinical_operations", "clinical_reasoning",
                "clinical_communication", "research_awareness",
            ]
            ordered = [d for d in coverage if d in selected]
            ordered.extend([d for d in selected if d not in ordered])
            return ordered

        # 湿实验：实验操作、质控、数据记录、结果解读优先
        if experience_type in ("wet_lab", "实验", "湿实验") or domain == "wet_lab":
            coverage = [
                "experiment_operation", "quality_control_lab", "data_recording",
                "result_interpretation_lab",
            ]
            ordered = [d for d in coverage if d in selected]
            ordered.extend([d for d in selected if d not in ordered])
            return ordered

    priority = ROLE_PRIORITY.get(role_category(target_role), [])
    ordered = [d for d in priority if d in selected]
    ordered.extend([d for d in selected if d not in ordered])
    return ordered


class MultiDimensionalContentGenerator:
    """基于事实驱动的通用多维简历要点生成器。

    生成流程：
      1. 读取 Canonical Experience；
      2. 判断经历类型；
      3. 找出已确认可用事实；
      4. 从医学维度集合中选择适用维度（事实门控）；
      5. 按目标岗位排序；
      6. 为每个维度生成一条独立内容；
      7. 检查重复与事实来源；
      8. 信息不足时把缺口写入 metadata 交给 Question Planner。

    本类不依赖任何黄金样例内容；不同经历、主题、工具、责任和岗位自然泛化。
    """

    def __init__(self, dimensions_config_path: Optional[str | Path] = None):
        if dimensions_config_path is None:
            dimensions_config_path = self._find_dimensions_config()

        with open(dimensions_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.dimensions = config["medical_knowledge_dimensions"]

        # 向后兼容属性：既有测试引用这些名称
        self.chinese_term_mapping = dict(TERM_MAP)
        self.action_verb_mapping = {
            "participated": ["参与", "协助"],
            "owned_component": ["负责", "完成"],
            "led_delivery": ["主导", "领导"],
            "project_owner": ["负责", "管理"],
        }
        self.value_expressions = {
            "quality_assurance": ["确保", "保障", "维护", "保证", "强化"],
            "impact_creation": ["形成", "建立", "构建", "创造", "发展"],
            "process_support": ["支持", "协助", "促进", "配合", "参与"],
            "outcome_driving": ["推动", "驱动", "引领", "促进", "贡献"],
            "capability_building": ["培养", "发展", "提升", "强化", "锻炼"],
        }

    def _find_dimensions_config(self) -> Path:
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data" / "medical-knowledge-dimensions.json",
            Path(__file__).parent.parent.parent / "data" / "medical-knowledge-dimensions.json",
            Path("data") / "medical-knowledge-dimensions.json",
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return Path(__file__).parent.parent.parent.parent / "data" / "medical-knowledge-dimensions.json"

    # ------------------------------------------------------------------
    # 通用事实提取器
    # ------------------------------------------------------------------
    def _goal(self, exp: Dict[str, Any]) -> str:
        return str(exp.get("problem_or_goal", "")).strip() or str(exp.get("background", "")).strip()

    def _team(self, exp: Dict[str, Any]) -> str:
        team = join_items(exp, "collaboration")
        return team if team else "课题团队"

    def _stat_tools(self, exp: Dict[str, Any]) -> str:
        tools = [t for t in to_list(exp, "tools") if t.lower() in STAT_TOOLS]
        return "、".join(cn(t) for t in tools[:3]) if tools else ""

    def _databases(self, exp: Dict[str, Any]) -> str:
        # 只返回数据库名称（不返回 workflow 里的整句，避免动词重复）
        dbs = [t for t in to_list(exp, "tools") if t.lower() in DATABASE_TOOLS]
        dbs = dbs or to_list(exp, "databases_used")
        return "、".join(cn(t) for t in dbs[:4]) if dbs else ""

    def _strip_leading_verb(self, text: str) -> str:
        """去除事实短语开头已带有的动作动词（完成/执行/实施/应用/使用/获得等）。"""
        return re.sub(r"^(完成|执行|实施|进行|应用|使用|协助|参与|开展|保障|获得|取得)", "", text).strip()

    def _screening(self, exp: Dict[str, Any]) -> str:
        hits = pick_hits(exp, ["quality_control", "workflow_steps", "screening_process"], "筛选", "纳入", "排除")
        if hits:
            return self._strip_leading_verb(hits[0])
        return "标题摘要初筛与全文复筛两级筛选"

    def _bias_tools(self, exp: Dict[str, Any]) -> str:
        hits = pick_hits(exp, ["quality_control", "quality_assessment", "bias_assessment"], "偏倚", "RoB")
        if not hits:
            return "偏倚风险评价工具"
        text = self._strip_leading_verb(hits[0])
        # 若形如 "应用X进行偏倚风险评价"，只保留工具名 X
        m = re.search(r"(?:应用|使用)?(.+?)(?:进行|完成)?(?:偏倚风险评价|风险评估)", text)
        if m:
            inner = m.group(1).strip()
            if inner:
                return inner
        return text

    def _extraction(self, exp: Dict[str, Any]) -> str:
        # 优先返回提取工具名；字段值可能形如"标准化表格提取基线特征…"，
        # 此时只取开头工具名，避免句子重复"提取"
        direct = str(exp.get("data_extraction", "")).strip()
        if direct:
            m = re.match(r"^([^提取]+)", direct)
            if m:
                return m.group(1).strip()
            return direct
        hits = pick_hits(exp, ["workflow_steps", "quality_control"], "提取", "表格", "结构化")
        if hits:
            return self._strip_leading_verb(hits[0])
        return "标准化表格"

    def _authorship(self, exp: Dict[str, Any]) -> str:
        for item in to_list(exp, "outcomes"):
            if any(t in item for t in ["作者", "论文", "在投", "发表", "投稿"]):
                return item
        return ""

    def _insight(self, exp: Dict[str, Any]) -> str:
        return join_items(exp, "insights", "；")

    def _study_count(self, exp: Dict[str, Any]) -> str:
        return scope_value(exp, "study_count")

    def _conditions(self, exp: Dict[str, Any]) -> str:
        # scope.main_conditions 可能是 list 或逗号分隔字符串
        scope = exp.get("scope", {}) or {}
        cond = scope.get("main_conditions")
        if isinstance(cond, list) and cond:
            return "、".join(str(c) for c in cond)
        if isinstance(cond, str) and cond.strip():
            return cond
        items = to_list(exp, "main_conditions")
        if items:
            return "、".join(items)
        return str(exp.get("patient_cases", "")).strip()

    def _clinical_skills(self, exp: Dict[str, Any]) -> str:
        return join_items(exp, "clinical_skills", "；")

    def _aux_exams(self, exp: Dict[str, Any]) -> str:
        # 优先使用明确的辅助检查条目；仅当没有时才回退到工具列表
        explicit = to_list(exp, "auxiliary_exams")
        if explicit:
            return "、".join(explicit[:4])
        hits = pick_hits(exp, ["tools"], "心电图", "超声", "影像", "实验室")
        return "、".join(hits[:4])

    def _operations(self, exp: Dict[str, Any]) -> str:
        ops = to_list(exp, "basic_operations")
        if ops:
            return "、".join(ops[:4])
        hits = pick_hits(exp, ["tools"], "采血", "心电图", "生命体征")
        return "、".join(hits[:4]) if hits else ""

    def _inspiration(self, exp: Dict[str, Any]) -> str:
        return str(exp.get("research_inspiration", "")).strip()

    def _recommendation(self, exp: Dict[str, Any]) -> str:
        direct = str(exp.get("recommendations", "")).strip()
        if direct:
            return direct
        hits = pick_hits(exp, ["outputs", "outcomes"], "建议")
        return self._strip_leading_verb(hits[0]) if hits else ""

    def _finding(self, exp: Dict[str, Any]) -> str:
        finding = str(exp.get("key_findings", "")).strip()
        if finding:
            return finding
        hits = pick_hits(exp, ["insights"], "发现", "认知", "不足")
        return hits[0] if hits else ""

    def _report_outcome(self, exp: Dict[str, Any]) -> str:
        hits = pick_hits(exp, ["outcomes", "outputs"], "结题", "优秀", "汇报", "答辩")
        if not hits:
            return ""
        return self._strip_leading_verb(hits[0])

    # ------------------------------------------------------------------
    # 责任动词（责任事实决定参与度，表达层级决定力度，二者分离）
    # ------------------------------------------------------------------
    def _responsibility_verb(self, exp: Dict[str, Any], tier: str) -> str:
        level = exp.get("role", {}).get("responsibility_level", "participated")
        if level in ("led_delivery", "project_owner"):
            if tier == "conservative":
                return "承担"
            return "主导"
        if level == "owned_component":
            return "负责"
        # participated
        if tier == "conservative":
            return "参与"
        if tier == "high_impact":
            return "深度参与"
        return "参与"

    def _value_phrase(self, dimension: str, tier: str, level: str) -> str:
        """按表达层级给出价值尾句（与责任事实分离，不升级责任）。"""
        if level in ("led_delivery", "project_owner"):
            return {"conservative": "为项目提供稳定支撑", "professional": "推动研究流程规范化", "high_impact": "带动研究流程高效落地"}[tier]
        if tier == "conservative":
            return "为项目提供基础支撑"
        if tier == "high_impact":
            return "为研究质量与进度提供有力保障"
        return "为研究质量与进度提供可靠保障"

    # ------------------------------------------------------------------
    # 各维度内容生成
    # ------------------------------------------------------------------
    def _generate_dimension_content(
        self, exp: Dict[str, Any], dimension: str, tier: str, target_role: str
    ) -> str:
        verb = self._responsibility_verb(exp, tier)
        level = exp.get("role", {}).get("responsibility_level", "participated")
        value = self._value_phrase(dimension, tier, level)
        goal = self._goal(exp)

        # --- 研究 / 系统综述维度 ---
        if dimension == "research_question":
            if not goal:
                return ""
            return f"围绕{goal}，{verb}研究问题的界定与梳理，明确研究边界和临床意义"

        if dimension == "pico_framework":
            return f"在导师指导下参与构建PICO研究框架，明确人群、干预、对照与结局等要素，为后续检索与筛选提供结构化依据"

        if dimension == "search_strategy":
            return f"{verb}制定系统检索策略，设计主题词与自由词组合，确保检索覆盖全面"

        if dimension == "database_retrieval":
            dbs = self._databases(exp)
            scope_count = scope_value(exp, "database_count")
            if dbs:
                suffix = f"（覆盖{scope_count}个数据库）" if scope_count else ""
                return f"{verb}制定并执行{dbs}多数据库检索策略{suffix}，{value}"
            if scope_count:
                return f"{verb}多数据库检索策略的执行（覆盖{scope_count}个数据库），{value}"
            return f"{verb}多数据库检索策略的制定与执行，保障文献检索的全面性"

        if dimension == "study_screening":
            screening = self._screening(exp)
            count = self._study_count(exp)
            suffix = f"，纳入{count}篇研究" if count else ""
            return f"{verb}完成{screening}，处理筛选分歧，保障纳入研究的质量一致性{suffix}"

        if dimension == "inclusion_exclusion":
            return f"{verb}制定明确的纳入与排除标准，规范筛选边界，减少主观偏倚"

        if dimension == "bias_assessment":
            tool = self._bias_tools(exp)
            return f"{verb}应用{tool}对纳入研究进行偏倚风险评价，确保证据基础的可靠性"

        if dimension == "data_extraction":
            tool = self._extraction(exp)
            return f"{verb}使用{tool}提取研究关键数据，维护结构化数据集，保障数据完整性与一致性"

        if dimension == "statistical_analysis":
            methods = set(exp.get("methods", []))
            is_epidemiology = bool(methods & {"cross_sectional_survey", "descriptive_statistics", "logistic_regression"})
            is_wetlab = bool(methods & {"cell_culture", "qPCR", "pcr", "western_blot"})
            if is_epidemiology:
                return f"{verb}根据数据特征选择描述性统计、卡方检验与回归分析等方法，确保结果的科学性"
            if is_wetlab:
                return f"{verb}实验数据的统计分析，评估组间差异与结果的显著性"
            tools = self._stat_tools(exp)
            tool_part = f"（使用{tools}）" if tools else ""
            return f"{verb}数据分析工作{tool_part}，评估异质性与结果稳定性，深入理解研究结果的临床意义"

        if dimension == "heterogeneity_interpretation":
            return f"{verb}异质性评价与敏感性分析等关键统计判断，理解治疗效果差异的可能来源"

        if dimension == "result_interpretation":
            return f"{verb}主要研究结果的解释，结合临床背景理解证据的适用范围与局限"

        if dimension == "manuscript_contribution":
            authorship = self._authorship(exp)
            if authorship:
                return f"作为{authorship}，{verb}论文撰写与修改，负责方法学描述和结果呈现"
            return f"{verb}论文撰写与修改，负责方法学描述和结果呈现"

        if dimension == "academic_presentation":
            return f"定期完成研究进展汇报，清晰传达研究发现与方法学考虑"

        if dimension == "collaboration":
            team = self._team(exp)
            return f"{verb}与{team}的有效协作，{value}"

        if dimension == "methodology_insight":
            insight = self._insight(exp)
            if insight:
                return f"深入理解{insight}，培养循证研究思维和科研问题识别能力"
            return f"在项目实践中加深对研究方法学的理解，{value}"

        # --- 大创 / 流行病学维度 ---
        if dimension == "questionnaire_design":
            return f"{verb}结构化问卷的设计与预调查，结合反馈完善条目设置和题项表达"

        if dimension == "data_collection":
            return f"{verb}较大规模问卷数据收集，保障回收数量与质量"

        if dimension == "quality_control":
            qc = join_items(exp, "quality_control")
            if not qc:
                qc = "双人录入和逻辑校验双重质量控制"
            return f"{verb}实施{qc}，保障数据准确性与结果可靠性"

        if dimension == "results_application":
            finding = self._finding(exp)
            recommendation = self._recommendation(exp)
            if finding and recommendation:
                return f"发现{finding}，提出{recommendation}，体现研究的实际应用价值"
            if finding:
                return f"发现{finding}，并结合结果提出改进方向，体现研究的实际价值"
            return f"参与研究结果的应用分析，提出有针对性的改进建议"

        if dimension == "project_report":
            outcome = self._report_outcome(exp)
            if outcome:
                return f"{verb}项目结题报告撰写与答辩汇报，项目最终获得{outcome}"
            return f"{verb}项目结题报告撰写与成果汇报"

        # --- 临床维度 ---
        if dimension == "clinical_domain":
            conditions = self._conditions(exp)
            cond_part = f"（主要病种：{conditions}）" if conditions else ""
            return f"跟随主治医师参与住院患者的日常诊疗与病情观察{cond_part}，培养专科临床思维"

        if dimension == "medical_history_exam":
            skills = self._clinical_skills(exp)
            return f"{verb}病史采集与体格检查，规范完成临床文档记录"

        if dimension == "ward_rounds":
            return f"{verb}查房前信息整理、病历书写与治疗方案讨论，锻炼临床推理能力"

        if dimension == "auxiliary_exams":
            exams = self._aux_exams(exp)
            exam_part = f"（如{exams}）" if exams else ""
            return f"协助整理与解读多维度辅助检查结果{exam_part}，理解综合诊疗决策过程"

        if dimension == "clinical_operations":
            ops = self._operations(exp)
            op_part = f"（如{ops}）" if ops else ""
            return f"在规范指导下完成基础临床操作{op_part}，建立扎实的临床技能基础"

        if dimension == "clinical_reasoning":
            return f"{verb}病例分析与鉴别诊断讨论，提升临床推理与决策能力"

        if dimension == "clinical_communication":
            return f"积极参与病例讨论与健康教育活动，提升医患沟通与团队协作能力"

        if dimension == "research_awareness":
            inspiration = self._inspiration(exp)
            if inspiration:
                return f"观察到{inspiration}，深入思考其循证依据，形成科研问题意识"
            return f"在临床实践中关注诊疗差异与循证依据，培养科研问题识别能力"

        # --- 湿实验维度 ---
        if dimension == "experiment_operation":
            return f"{verb}核心实验流程的操作，规范执行实验方案并记录过程"

        if dimension == "quality_control_lab":
            qc = join_items(exp, "quality_control")
            return f"{verb}实施{qc}，保障实验数据的可靠性与可重复性"

        if dimension == "data_recording":
            return f"规范完成实验数据记录与整理，保障数据完整可追溯"

        if dimension == "result_interpretation_lab":
            return f"{verb}实验结果的分析与解读，结合实验背景判断结果的可靠性"

        # --- 兜底维度（信息极少时的简短初稿，不虚构细节） ---
        if dimension == "research_workflow":
            actions = to_list(exp, "actions")
            methods = to_list(exp, "methods")
            tools = to_list(exp, "tools")
            parts = []
            if methods:
                parts.append("、".join(cn(m) for m in methods[:2]))
            if actions:
                parts.append("、".join(cn(a) for a in actions[:2]))
            if tools:
                parts.append("使用" + "、".join(cn(t) for t in tools[:2]))
            body = "，".join(parts)
            if not body:
                return ""
            return f"{verb}{body}，{value}"

        return ""

    def _build_claim(
        self,
        exp: Dict[str, Any],
        dimension: str,
        wording: str,
        target_role: str,
        tier: str,
        used_facts: List[str],
    ) -> BulletClaim:
        experience_id = exp.get("experience_id", "unknown")
        evidence_ids = tuple(exp.get("evidence_ids", []))
        responsibility_level = exp.get("role", {}).get("responsibility_level", "participated")

        return BulletClaim(
            claim_id=f"claim_{experience_id}_{dimension}_{tier}",
            experience_id=experience_id,
            role_pack=target_role,
            wording=wording,
            used_facts=tuple(used_facts),
            evidence_ids=evidence_ids,
            responsibility_level=responsibility_level,
            omitted_unknowns=tuple(exp.get("unknowns", [])),
            risk_flags=self._assess_risks(wording, responsibility_level, tier),
            dimension_id=dimension,
            claim_type="experience",
            expression_tier=tier,
            source_fact_ids=used_facts,
            role_value=role_value_text(dimension, target_role),
            verification_status="candidate",
        )

    def _extract_used_facts(self, wording: str, exp: Dict[str, Any]) -> List[str]:
        """提取实际用于措辞的事实（field:item 格式，与三档事实校验兼容）。"""
        used = []
        array_fields = [
            "actions", "methods", "tools", "objects", "collaboration",
            "artifacts", "outcomes", "workflow_steps", "quality_control",
            "decisions_or_judgments", "difficulties", "insights",
            "capability_evidence", "outputs", "clinical_skills",
            "basic_operations", "auxiliary_exams",
        ]
        for field in array_fields:
            for item in to_list(exp, field):
                item_str = str(item)
                mapped = cn(item_str)
                if mapped in wording or item_str in wording:
                    used.append(f"{field}:{item_str}")
        # 字符串事实
        for field in ["problem_or_goal", "background", "key_findings", "recommendations",
                      "research_inspiration", "results_interpretation", "data_extraction"]:
            value = exp.get(field)
            if isinstance(value, str) and value.strip() and value in wording:
                used.append(f"{field}:{value}")
        return used

    def _assess_risks(self, wording: str, responsibility_level: str, tier: str) -> List[str]:
        risks = []
        upgrade_indicators = {
            "participated": ["负责", "主导", "领导", "管理", "独立"],
            "owned_component": ["主导", "领导", "管理整体", "独立负责整体"],
            "led_delivery": ["整体负责", "全面领导"],
        }
        for indicator in upgrade_indicators.get(responsibility_level, []):
            if indicator in wording:
                risks.append(f"implies higher responsibility: {indicator}")
        return risks

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def generate_content(
        self,
        *,
        canonical_experience: Dict[str, Any],
        content_plan: Dict[str, Any],
        target_role: str,
        expression_tier: str = "professional",
    ) -> ContentGenerationResult:
        if not canonical_experience:
            raise ValueError("需要提供标准化经历记录")
        if not content_plan:
            raise ValueError("需要提供内容计划")
        if expression_tier not in ["conservative", "professional", "high_impact"]:
            raise ValueError("表达层级必须是 conservative, professional, 或 high_impact")

        experience_id = canonical_experience.get("experience_id", "unknown")
        evidence_ids = tuple(canonical_experience.get("evidence_ids", []))
        target_bullet_count = int(content_plan.get("bullet_count_target", 5) or 5)

        # 1. 事实驱动选择维度 -> 按经历类型与岗位排序
        selected = plan_dimensions(canonical_experience)
        ordered = order_dimensions(selected, target_role, canonical_experience)

        # 2. 项目概述（若经历信息足够丰富且目标数有富余）
        bullet_claims: List[BulletClaim] = []
        if self._should_generate_overview(canonical_experience, target_bullet_count):
            overview = self._generate_project_overview(
                canonical_experience, target_role, expression_tier
            )
            if overview:
                bullet_claims.append(overview)

        # 3. 逐维度生成
        for dimension in ordered:
            if len(bullet_claims) >= target_bullet_count:
                break
            wording = self._generate_dimension_content(
                canonical_experience, dimension, expression_tier, target_role
            )
            if not wording or not wording.strip():
                continue
            used_facts = self._extract_used_facts(wording, canonical_experience)
            bullet_claims.append(
                self._build_claim(
                    canonical_experience, dimension, wording.strip(),
                    target_role, expression_tier, used_facts,
                )
            )

        # 4. 信息极少：兜底维度生成简短初稿（不虚构细节）
        if len(bullet_claims) < min(2, target_bullet_count):
            fallback_wording = self._generate_dimension_content(
                canonical_experience, "research_workflow", expression_tier, target_role
            )
            if fallback_wording:
                used_facts = self._extract_used_facts(fallback_wording, canonical_experience)
                bullet_claims.append(
                    self._build_claim(
                        canonical_experience, "research_workflow", fallback_wording.strip(),
                        target_role, expression_tier, used_facts,
                    )
                )

        # 5. 记录缺口（交给 Question Planner）
        missing = missing_dimensions(canonical_experience, ordered)

        generation_metadata = {
            "generated_dimensions": [c.dimension_id for c in bullet_claims],
            "actual_bullet_count": len(bullet_claims),
            "target_bullet_count": target_bullet_count,
            "expression_tier": expression_tier,
            "responsibility_level": canonical_experience.get("role", {}).get("responsibility_level", "participated"),
            "generation_strategy": "fact_driven_dimension_planning",
            "selected_dimensions": ordered,
            "missing_dimensions": missing,
        }

        return ContentGenerationResult(
            experience_id=experience_id,
            target_role=target_role,
            expression_tier=expression_tier,
            bullet_claims=bullet_claims,
            generation_metadata=generation_metadata,
        )

    def _should_generate_overview(self, exp: Dict[str, Any], target_bullet_count: int) -> bool:
        # 仅研究类经历且信息充分、目标数有富余时生成概述；
        # 临床/大创/湿实验等经历的所有槽位都用于核心覆盖维度。
        domain = exp.get("context", {}).get("domain", "")
        if domain != "clinical_research":
            return False
        info_richness = len([v for v in exp.values() if v])
        return info_richness >= 8 and target_bullet_count >= 7

    def _generate_project_overview(
        self, exp: Dict[str, Any], target_role: str, tier: str
    ) -> Optional[BulletClaim]:
        context = exp.get("context", {})
        topic = str(context.get("topic", "")).strip()
        goal = self._goal(exp)
        team = self._team(exp)

        if not topic:
            methods = to_list(exp, "methods")
            if methods:
                topic = "、".join(cn(m) for m in methods[:2])
            else:
                domain = context.get("domain", "")
                topic = "相关临床与研究项目" if domain == "clinical_practice" else "相关科研项目"

        if tier == "conservative":
            overview = f"与{team}协作参与{topic}"
        elif tier == "high_impact":
            overview = f"深度参与{topic}，在团队协作中建立系统性专业能力"
        else:
            overview = f"参与{topic}，在团队协作中承担具体工作环节"

        if goal:
            overview += f"，旨在{goal}"

        used_facts = self._extract_used_facts(overview, exp)
        return self._build_claim(exp, "project_overview", overview, target_role, tier, used_facts)


# 示例用法
if __name__ == "__main__":
    generator = MultiDimensionalContentGenerator()

    sample = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "sample_meta_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "某项系统综述研究"},
        "role": {"responsibility_level": "participated", "personal_boundary": "在导师指导下参与检索与筛选"},
        "background": "治疗方案的临床争议",
        "problem_or_goal": "比较不同治疗方案的效果",
        "actions": ["retrieve_literature", "screen_studies", "extract_data"],
        "methods": ["systematic_review"],
        "tools": ["pubmed", "embase", "cochrane"],
        "quality_control": ["标题摘要初筛与全文复筛两级筛选", "偏倚风险评价"],
        "outputs": ["研究数据库", "统计分析结果"],
        "scope": {"database_count": "3", "study_count": "40"},
        "status": "user_confirmed",
    }

    plan = {
        "experience_id": "sample_meta_001",
        "bullet_count_target": 8,
        "evidence_ids": ["ev_001"],
    }

    result = generator.generate_content(
        canonical_experience=sample,
        content_plan=plan,
        target_role="doctoral_v1",
        expression_tier="professional",
    )
    for c in result.bullet_claims:
        print(f"[{c.dimension_id}] {c.wording}")
    print("missing:", result.generation_metadata["missing_dimensions"])
