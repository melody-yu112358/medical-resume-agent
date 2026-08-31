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
        "verify_research_quality": "研究质量复核",
        "resolve_workflow_issue": "处理流程问题",
        "prepare_research_outputs": "整理研究交付物",
        "perform_analysis": "统计分析",
        "write_manuscript": "论文材料撰写",
        "culture_cells": "细胞培养",
        "perform_qpcr": "qPCR 实验",
        "perform_western_blot": "Western Blot 实验",
        "review_clinical_case": "病例分析",
        "prepare_case_presentation": "准备病例汇报",
        "retrieve_guidelines": "临床指南检索",
        "join_ward_rounds": "参与临床查房",
        "collect_medical_history": "病史采集",
        "perform_physical_examination": "体格检查",
        "review_patient_records": "病历资料查阅与整理",
        "interpret_clinical_findings": "检查与检验结果分析",
        "document_clinical_work": "临床记录书写",
        "communicate_with_patients": "患者沟通与健康宣教",
        "support_clinical_procedure": "临床操作观摩或协助",
        "handover_clinical_information": "病例信息交接",
        "follow_clinical_safety": "医疗安全与规范执行",
        "collaborate_clinical_team": "临床团队协作",
        "incorporate_clinical_feedback": "根据带教反馈改进",
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
        "clinical_note": "临床记录",
        "case_summary": "病例总结",
        "patient_education_material": "患者宣教材料",
        "rotation_report": "轮转总结",
    },
    "collaboration": {
        "research_team": "课题组",
        "supervisor": "导师",
        "peer": "同学 / 团队成员",
        "clinician": "临床医生",
        "statistician": "统计 / 数据人员",
        "attending_physician": "带教 / 上级医师",
        "nurse": "护理人员",
        "patient_or_family": "患者 / 家属",
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
