from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any


def create_v32_synthetic_demo_experiences(candidate_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create the frozen synthetic V3.2 demo records.

    The constants below belong only to the de-identified golden fixture. Real
    user flows must build canonical records item by item from confirmed facts
    and must not call this factory.
    """

    # Meta Analysis Experience
    meta_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "meta_analysis_001",
        "evidence_ids": ["ev_meta_001"],
        "organization": candidate_facts["meta_analysis_experience"]["organization"],
        "title": candidate_facts["meta_analysis_experience"]["title"],
        "department_or_field": candidate_facts["meta_analysis_experience"]["department"],
        "period": candidate_facts["meta_analysis_experience"]["period"],
        "context": {
            "domain": "clinical_research",
            "setting": "research_project",
            "topic": "心血管Meta分析"
        },
        "role": {
            "title": "研究助理",
            "responsibility_level": "participated",
            "personal_boundary": "在导师指导下参与文献检索和筛选工作"
        },
        "background": "急性冠脉综合征患者对抗血小板治疗的反应存在差异",
        "problem_or_goal": "通过系统性证据综合比较不同抗血小板药物在ACS患者中的疗效",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r", "endnote", "noteexpress"],
        "objects": ["医学文献", "临床研究"],
        "databases_used": ["PubMed", "Embase", "Cochrane"],
        "data_extraction": "标准化表格提取基线特征、干预措施、结局指标",
        "results_interpretation": "能够解释主要结果和异质性来源",
        "presentation": "3次组会汇报",
        "workflow_steps": [
            "在导师指导下制定PICO研究框架",
            "执行多数据库检索策略",
            "完成两级筛选流程",
            "使用标准化表格提取结构化数据"
        ],
        "quality_control": [
            "标题摘要初筛和全文复筛双重筛选",
            "应用Cochrane RoB工具进行偏倚风险评价",
            "使用标准化数据提取表格"
        ],
        "decisions_or_judgments": [
            "通过团队讨论解决筛选分歧",
            "基于异质性选择适当的统计模型"
        ],
        "difficulties": [
            "处理大量检索到的研究",
            "解决纳入标准模糊的案例"
        ],
        "collaboration": ["研究团队", "导师"],
        "artifacts": ["PRISMA流程图", "数据提取表"],
        "outputs": ["45篇纳入研究的高质量结构化数据库", "统计分析结果"],
        "outcomes": ["作为第三作者参与论文撰写（在投）"],
        "insights": [
            "理解严格方法学在证据综合中的重要性",
            "认识治疗效果异质性的临床意义"
        ],
        "capability_evidence": [
            "展示了系统性文献检索能力",
            "一致应用PRISMA指南",
            "适当使用Cochrane RoB工具"
        ],
        "role_relevance": "直接符合博士研究方法学要求",
        "research_interest_link": "与心血管二级预防优化研究兴趣相关",
        "scope": {
            "database_count": "3",
            "study_count": "45",
            "time_period": "2022-2024"
        },
        "status": "user_confirmed"
    }

    # Innovation Project (大创) Experience
    innovation_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "innovation_project_001",
        "evidence_ids": ["ev_innovation_001"],
        "organization": candidate_facts["education"]["institution"],
        "title": candidate_facts["innovation_project"]["title"],
        "department_or_field": candidate_facts["innovation_project"]["project_type"],
        "period": candidate_facts["innovation_project"]["period"],
        "context": {
            "domain": "epidemiology_research",
            "setting": "university_research_project",
            "topic": "医学生心血管疾病认知现状调查"
        },
        "role": {
            "title": "研究团队成员",
            "responsibility_level": "participated",
            "personal_boundary": "在导师指导下参与问卷设计和数据收集"
        },
        "background": "医学生对心血管疾病预防的认知不足",
        "problem_or_goal": "评估医学生心血管疾病认知水平并识别知识缺口",
        "actions": ["design_questionnaire", "collect_data", "analyze_data", "interpret_results"],
        "methods": ["cross_sectional_survey", "descriptive_statistics", "logistic_regression"],
        "tools": ["SPSS", "Excel"],
        "objects": ["调查问卷", "医学生队列"],
        "sample_size": "300+",
        "key_findings": "高年级医学生对二级预防认知显著不足",
        "recommendations": "针对性教学改进建议",
        "workflow_steps": [
            "设计结构化问卷并进行预调查验证",
            "实施双人录入质量控制",
            "进行描述性和推断性统计分析",
            "解释发现并提出建议"
        ],
        "quality_control": [
            "预调查问卷验证",
            "双人录入和逻辑校验",
            "选择适当的统计方法"
        ],
        "decisions_or_judgments": [
            "根据预调查反馈完善问卷条目",
            "根据数据特征选择适当的统计检验"
        ],
        "difficulties": [
            "获得足够的问卷回收率",
            "处理调查中的缺失数据"
        ],
        "collaboration": ["研究团队", "导师"],
        "artifacts": ["验证后的问卷", "清洗后的数据集", "分析报告"],
        "outputs": ["300+份完成的调查", "统计分析结果", "建议报告"],
        "outcomes": ["获得校级优秀结题评价"],
        "insights": [
            "理解调查方法学和质量控制的重要性",
            "认识研究成果对教育改进的价值"
        ],
        "capability_evidence": [
            "展示了调查设计和实施能力",
            "应用了适当的统计分析方法",
            "参与了研究报告和建议撰写"
        ],
        "role_relevance": "与流行病学研究和公共卫生方法学相关",
        "research_interest_link": "与心血管疾病预防教育研究兴趣相关",
        "scope": {
            "sample_size": "300+",
            "time_period": "2021-2022"
        },
        "status": "user_confirmed"
    }

    # Clinical Internship Experience
    clinical_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "clinical_internship_001",
        "evidence_ids": ["ev_clinical_001"],
        "organization": candidate_facts["clinical_internship"]["hospital"],
        "title": candidate_facts["clinical_internship"]["department"] + "临床实习",
        "department_or_field": candidate_facts["clinical_internship"]["department"],
        "period": candidate_facts["clinical_internship"]["period"],
        "context": {
            "domain": "clinical_practice",
            "setting": "hospital_ward",
            "topic": "心内科临床实习"
        },
        "role": {
            "title": "医学实习生",
            "responsibility_level": "participated",
            "personal_boundary": "在主治医师直接指导下参与患者诊疗活动"
        },
        "background": "临床实践为循证医学理解提供基础",
        "problem_or_goal": "培养临床技能并理解医学知识的实际应用",
        "actions": ["collect_patient_history", "perform_physical_exam", "interpret_auxiliary_exams", "participate_in_case_discussions"],
        "methods": ["clinical_assessment", "differential_diagnosis", "treatment_planning"],
        "tools": ["心电图", "生命体征监测仪", "电子病历系统"],
        "objects": ["心脏病患者", "临床病例"],
        "main_conditions": ["冠心病", "心衰"],
        "patient_cases": "20+住院患者",
        "clinical_skills": [
            "跟随主治医师参与日常管理",
            "参与查房前信息整理",
            "病历书写",
            "治疗方案讨论"
        ],
        "auxiliary_exams": [
            "心电图解读",
            "心脏超声解读",
            "实验室检查整合"
        ],
        "basic_operations": [
            "静脉采血",
            "心电图",
            "生命体征监测"
        ],
        "research_inspiration": "观察到抗血小板药物使用的显著个体差异，深入思考其循证依据",
        "workflow_steps": [
            "查房前准备患者信息",
            "参与病史采集和体格检查",
            "在指导下解读辅助检查",
            "参与病例讨论和治疗方案制定"
        ],
        "quality_control": [
            "所有患者互动均有导师监督",
            "标准化临床文档协议",
            "定期反馈和技能评估"
        ],
        "decisions_or_judgments": [
            "为病例汇报优先整理患者信息",
            "识别关键临床发现用于鉴别诊断"
        ],
        "difficulties": [
            "在繁忙的查房中有效管理时间",
            "与多样化患者群体有效沟通"
        ],
        "collaboration": ["主治医师", "住院医师", "护理人员"],
        "artifacts": ["患者病历", "病例汇报", "临床报告"],
        "outputs": ["20+例患者病例接触", "临床技能发展", "病例汇报"],
        "outcomes": ["增强临床推理和患者诊疗技能"],
        "insights": [
            "理解理论知识与临床实践的差距",
            "认识个体化治疗方案的重要性",
            "观察到抗血小板药物使用的实际差异"
        ],
        "capability_evidence": [
            "展示了基础临床技能能力",
            "显示了整合多源数据进行临床决策的能力",
            "发展了临床沟通技能"
        ],
        "role_relevance": "为临床研究和循证实践奠定基础",
        "research_interest_link": "启发了对循证心血管治疗优化的研究兴趣",
        "scope": {
            "patient_count": "20+",
            "main_conditions": ["冠心病", "心衰"],
            "time_period": "2023"
        },
        "status": "user_confirmed"
    }

    return [meta_experience, innovation_experience, clinical_experience]
