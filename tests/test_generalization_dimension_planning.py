# -*- coding: utf-8 -*-
"""
通用多维内容生成泛化测试

验证生成器对不同医学经历、研究主题、工具、责任和岗位的泛化能力，
不依赖任何黄金样例内容。对应开发要求"禁止过拟合黄金样例"。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from medical_career_agent.services.multi_dimensional_content_generator import (
    MultiDimensionalContentGenerator,
    plan_dimensions,
    missing_dimensions,
)


# ---------------------------------------------------------------------------
# 案例A：肿瘤Meta分析（不同疾病主题，无R、无论文）
# ---------------------------------------------------------------------------
TUMOR_META = {
    "schema_version": "canonical-experience-v1",
    "experience_id": "tumor_meta_001",
    "evidence_ids": ["ev_tumor_001"],
    "experience_type": "meta",
    "context": {"domain": "clinical_research", "setting": "research_project", "topic": "非小细胞肺癌靶向治疗的系统综述"},
    "role": {"responsibility_level": "participated", "personal_boundary": "在导师指导下参与文献检索和筛选"},
    "background": "非小细胞肺癌靶向治疗方案的临床选择存在争议",
    "problem_or_goal": "系统评价不同靶向药物对非小细胞肺癌患者的疗效差异",
    "actions": ["retrieve_literature", "screen_studies", "extract_data"],
    "methods": ["systematic_review"],
    "tools": ["pubmed", "embase"],
    "workflow_steps": ["制定检索策略", "多数据库检索", "两级筛选"],
    "quality_control": ["双人独立筛选", "纳入标准讨论"],
    "outputs": ["纳入研究汇总表"],
    "scope": {"study_count": "32"},
    "status": "user_confirmed",
}


def test_case_A_tumor_meta_no_leakage():
    """肿瘤Meta：不出现心血管/ACS/抗血小板/R/论文；生成内容仍专业。"""
    g = MultiDimensionalContentGenerator()
    plan = {"experience_id": "tumor_meta_001", "bullet_count_target": 7, "evidence_ids": ["ev_tumor_001"]}
    result = g.generate_content(
        canonical_experience=TUMOR_META, content_plan=plan,
        target_role="doctoral_v1", expression_tier="professional",
    )

    # 无黄金样例专有词泄漏
    golden_terms = ["心血管", "ACS", "抗血小板", "R", "SPSS", "论文", "第三作者"]
    for claim in result.bullet_claims:
        for term in golden_terms:
            assert term not in claim.wording, f"黄金词泄漏: {term} in {claim.wording}"

    # 内容仍然专业且覆盖不同维度
    assert len(result.bullet_claims) >= 4
    dims = [c.dimension_id for c in result.bullet_claims]
    assert len(set(dims)) == len(dims), "维度重复"

    # 每个维度都有事实支持（只选有事实的）
    assert any(d in dims for d in ["research_question", "database_retrieval", "study_screening"])

    # 缺少的分析和论文维度进入待补问题
    missing = missing_dimensions(TUMOR_META, plan_dimensions(TUMOR_META))
    assert "statistical_analysis" in missing or "result_interpretation" in missing


# ---------------------------------------------------------------------------
# 案例B：临床实习为主（无Meta）
# ---------------------------------------------------------------------------
RESPIRATORY_CLINICAL = {
    "schema_version": "canonical-experience-v1",
    "experience_id": "resp_clinical_001",
    "evidence_ids": ["ev_resp_001"],
    "experience_type": "clinical",
    "context": {"domain": "clinical_practice", "setting": "hospital_ward", "topic": "呼吸科临床实习"},
    "role": {"responsibility_level": "participated", "personal_boundary": "在带教医师指导下参与诊疗活动"},
    "actions": ["collect_patient_history", "write_medical_records"],
    "methods": ["clinical_assessment", "differential_diagnosis"],
    "tools": ["电子病历系统", "血氧仪"],
    "main_conditions": ["慢性阻塞性肺疾病", "肺炎"],
    "clinical_skills": ["病历书写", "体格检查", "查房记录"],
    "auxiliary_exams": ["胸部影像解读", "血气分析结果解读"],
    "quality_control": ["带教医师审核病历", "规范记录流程"],
    "workflow_steps": ["参与查房", "病历书写", "健康教育"],
    "patient_cases": "15+住院患者",
    "scope": {"patient_count": "15+"},
    "status": "user_confirmed",
}


def test_case_B_respiratory_clinical_no_meta():
    """呼吸科临床实习：不生成系统综述/PICO/偏倚风险内容。"""
    g = MultiDimensionalContentGenerator()
    plan = {"experience_id": "resp_clinical_001", "bullet_count_target": 5, "evidence_ids": ["ev_resp_001"]}
    result = g.generate_content(
        canonical_experience=RESPIRATORY_CLINICAL, content_plan=plan,
        target_role="doctoral_v1", expression_tier="professional",
    )

    forbidden_meta_terms = ["系统综述", "Meta分析", "PICO", "偏倚", "检索"]
    for claim in result.bullet_claims:
        for term in forbidden_meta_terms:
            assert term not in claim.wording, f"不应出现Meta内容: {term} in {claim.wording}"

    # 重点展示临床思维、规范、沟通和问题识别
    dims = [c.dimension_id for c in result.bullet_claims]
    assert any(d in dims for d in ["clinical_domain", "ward_rounds", "medical_history_exam"])
    assert any(d in dims for d in ["clinical_reasoning", "clinical_communication"])


# ---------------------------------------------------------------------------
# 案例C：湿实验经历
# ---------------------------------------------------------------------------
WETLAB = {
    "schema_version": "canonical-experience-v1",
    "experience_id": "wetlab_001",
    "evidence_ids": ["ev_wetlab_001"],
    "experience_type": "wet_lab",
    "context": {"domain": "wet_lab", "setting": "university_lab", "topic": "肿瘤细胞系药物敏感性实验"},
    "role": {"responsibility_level": "owned_component", "personal_boundary": "负责细胞培养与qPCR检测部分"},
    "actions": ["perform_experiments", "collect_samples"],
    "methods": ["cell_culture", "qPCR", "western_blot"],
    "tools": ["培养箱", "qPCR仪", "电泳仪"],
    "workflow_steps": ["细胞传代与培养", "qPCR检测", "Western blot分析"],
    "quality_control": ["设置复孔", "设置内参对照"],
    "outputs": ["qPCR表达数据", "蛋白条带图像"],
    "collaboration": ["课题组"],
    "scope": {},
    "status": "user_confirmed",
}


def test_case_C_wetlab_no_clinical_no_meta():
    """湿实验：生成实验设计/操作/质控/记录/协作，不生成临床管理或Meta内容。"""
    g = MultiDimensionalContentGenerator()
    plan = {"experience_id": "wetlab_001", "bullet_count_target": 5, "evidence_ids": ["ev_wetlab_001"]}
    result = g.generate_content(
        canonical_experience=WETLAB, content_plan=plan,
        target_role="health_ai_data_v1", expression_tier="professional",
    )

    forbidden = ["问卷", "查房", "Meta", "系统综述", "PICO", "偏倚"]
    for claim in result.bullet_claims:
        for term in forbidden:
            assert term not in claim.wording, f"不应出现其他类型内容: {term} in {claim.wording}"

    dims = [c.dimension_id for c in result.bullet_claims]
    assert any(d in dims for d in ["experiment_operation", "quality_control_lab", "data_recording"])


# ---------------------------------------------------------------------------
# 案例D：信息极少
# ---------------------------------------------------------------------------
MINIMAL_META = {
    "schema_version": "canonical-experience-v1",
    "experience_id": "minimal_meta_001",
    "evidence_ids": ["ev_min_001"],
    "context": {"domain": "clinical_research", "setting": "research_project"},
    "role": {"responsibility_level": "participated"},
    "actions": ["retrieve_literature"],
    "methods": ["meta_analysis"],
    "status": "user_confirmed",
}


def test_case_D_minimal_input_no_fabrication():
    """信息极少：只生成有事实支持的简短初稿，不虚构细节。"""
    g = MultiDimensionalContentGenerator()
    plan = {"experience_id": "minimal_meta_001", "bullet_count_target": 5, "evidence_ids": ["ev_min_001"]}
    result = g.generate_content(
        canonical_experience=MINIMAL_META, content_plan=plan,
        target_role="doctoral_v1", expression_tier="professional",
    )

    # 不自动增加数据库、R、PICO、论文和数字
    fabricated_terms = ["PubMed", "Embase", "R", "SPSS", "PICO", "论文", "45", "3个数据库"]
    for claim in result.bullet_claims:
        for term in fabricated_terms:
            assert term not in claim.wording, f"虚构内容: {term} in {claim.wording}"

    # 生成了简短初稿（至少1条）
    assert len(result.bullet_claims) >= 1

    # 缺口的分析/论文维度进入待补问题
    missing = missing_dimensions(MINIMAL_META, plan_dimensions(MINIMAL_META))
    assert any(d in missing for d in ["statistical_analysis", "manuscript_contribution", "database_retrieval"])


# ---------------------------------------------------------------------------
# 案例E：主题替换（黄金样例的词不应残留）
# ---------------------------------------------------------------------------
def test_case_E_topic_substitution_no_golden_leak():
    """将黄金fixture的主题/工具/论文状态替换后，输出随事实变化且无黄金词泄漏。"""
    # 替换主题为糖尿病、工具为Stata、无论文
    substituted = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "diabetes_meta_001",
        "evidence_ids": ["ev_dia_001"],
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "2型糖尿病降糖药物的系统综述"},
        "role": {"responsibility_level": "participated", "personal_boundary": "在导师指导下参与数据提取"},
        "background": "不同降糖药物对2型糖尿病患者血糖控制效果存在差异",
        "problem_or_goal": "系统评价不同降糖药物对糖化血红蛋白的影响",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["stata"],
        "quality_control": ["双重筛选", "纳入标准"],
        "scope": {"study_count": "28"},
        "status": "user_confirmed",
    }

    g = MultiDimensionalContentGenerator()
    plan = {"experience_id": "diabetes_meta_001", "bullet_count_target": 7, "evidence_ids": ["ev_dia_001"]}
    result = g.generate_content(
        canonical_experience=substituted, content_plan=plan,
        target_role="medical_affairs_v1", expression_tier="professional",
    )

    # 主题词应出现
    assert "糖尿病" in " ".join(c.wording for c in result.bullet_claims)

    # 黄金样例专有词不残留
    golden_terms = ["心血管", "ACS", "抗血小板", "SPSS", "R", "第三作者", "某附属医院", "某医科大学"]
    for claim in result.bullet_claims:
        for term in golden_terms:
            assert term not in claim.wording, f"黄金词泄漏: {term} in {claim.wording}"

    # 工具随事实变化
    assert "Stata" in " ".join(c.wording for c in result.bullet_claims)
