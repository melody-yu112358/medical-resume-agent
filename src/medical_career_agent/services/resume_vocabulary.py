from __future__ import annotations

from types import MappingProxyType
from typing import Mapping


_FACT_LABELS = {
    "actions": {
        "define_research_question": "明确研究问题",
        "develop_protocol": "制定或修改研究方案",
        "design_search_strategy": "设计检索式",
        "retrieve_literature": "医学文献检索",
        "screen_studies": "文献筛选",
        "extract_data": "数据提取",
        "create_flowchart": "绘制研究流程图",
        "assess_quality": "质量评价 / 偏倚评估",
        "perform_analysis": "统计分析",
        "write_manuscript": "论文材料撰写",
        "culture_cells": "细胞培养",
        "perform_qpcr": "qPCR 实验",
        "perform_western_blot": "Western Blot 实验",
        "review_clinical_case": "病例分析",
        "prepare_case_presentation": "准备病例汇报",
        "retrieve_guidelines": "临床指南检索",
    },
    "methods": {
        "systematic_review": "系统综述",
        "meta_analysis": "Meta 分析",
        "randomized_trial": "随机对照试验",
        "cohort_study": "队列研究",
        "case_control": "病例对照研究",
        "mendelian_randomization": "孟德尔随机化",
        "sensitivity_analysis": "敏感性分析",
    },
    "techniques": {
        "cell_culture": "细胞培养",
        "qpcr": "qPCR",
        "western_blot": "Western Blot",
        "flow_cytometry": "流式细胞术",
        "elisa": "ELISA",
        "animal_experiment": "动物实验",
    },
    "tools": {
        "r": "R",
        "python": "Python",
        "spss": "SPSS",
        "sql": "SQL",
        "stata": "Stata",
        "sas": "SAS",
        "excel": "Excel",
        "revman": "RevMan",
        "endnote": "EndNote",
        "noteexpress": "NoteExpress",
        "pubmed": "PubMed",
        "embase": "Embase",
        "cochrane": "Cochrane",
        "web_of_science": "Web of Science",
        "cnki": "中国知网 CNKI",
        "wanfang": "万方",
        "vip": "维普",
        "graphpad_prism": "GraphPad Prism",
    },
    "artifacts": {
        "prisma_flowchart": "PRISMA 流程图",
        "search_record": "检索式 / 检索记录",
        "screening_record": "筛选记录",
        "data_extraction_sheet": "数据提取表",
        "analysis_code": "分析代码",
        "research_paper": "论文材料",
        "analysis_figures": "分析图表",
        "research_report": "研究报告 / 汇报材料",
        "sop": "SOP / 流程文件",
        "group_presentation": "组会汇报",
        "case_presentation_material": "病例汇报材料",
    },
    "collaboration": {
        "research_team": "课题组",
        "supervisor": "导师",
    },
    "outcomes": {
        "no_publication_plan": "暂无发表计划",
        "materials_preparing": "正在整理材料",
        "submitted": "已经投稿",
        "under_review": "审稿中",
        "accepted": "已录用",
        "published": "已发表",
    },
}

FACT_LABELS: Mapping[str, Mapping[str, str]] = MappingProxyType({
    category: MappingProxyType(labels) for category, labels in _FACT_LABELS.items()
})


def flat_fact_labels() -> dict[str, str]:
    """Return a flat, JSON-safe view for consumers that do not group facts."""
    return {
        fact_id: label
        for category in FACT_LABELS.values()
        for fact_id, label in category.items()
    }
