"""Backend-owned answer guidance for the existing resume conversation.

The catalog suggests common medical-resume answers without asserting that any
option is true. Selected labels return to the normal conversation endpoint as
explicit user input and still pass through extraction and confirmation gates.
"""
from __future__ import annotations

from typing import Any


def _option(option_id: str, label: str, answer_text: str | None = None) -> dict[str, str]:
    return {"id": option_id, "label": label, "answer_text": answer_text or label}


class QuestionGuidanceService:
    """Translate one pending question into a stable, non-evidentiary UI card."""

    _UNKNOWN = _option("unknown", "不确定 / 不记得", "这项信息我目前不确定或不记得。")

    @classmethod
    def build(cls, question: str | None, *, stage: str) -> dict[str, Any] | None:
        text = str(question or "").strip()
        if not text or stage != "fact_confirmation":
            return None

        normalized = text.lower()
        if any(term in normalized for term in ("科室或场景", "哪类病例")):
            card = cls._clinical_setting(text)
        elif any(term in normalized for term in ("临床实践中实际参与", "哪些临床任务")):
            card = cls._clinical_tasks(text)
        elif any(term in normalized for term in ("病例分析", "检查结果解读", "指南查阅")):
            card = cls._clinical_reasoning(text)
        elif any(term in normalized for term in ("临床记录", "病例总结")):
            card = cls._clinical_outputs(text)
        elif any(term in normalized for term in ("医疗安全", "感染防控", "隐私规范")):
            card = cls._clinical_safety(text)
        elif any(term in normalized for term in ("临床实践中与哪些人员", "协作或沟通")):
            card = cls._clinical_collaboration(text)
        elif any(term in normalized for term in ("带教反馈", "改进了哪项")):
            card = cls._clinical_learning(text)
        elif any(term in normalized for term in ("数据库", "文献检索")):
            card = cls._databases(text)
        elif any(term in normalized for term in ("文献筛选", "数据提取", "质量评价", "哪些环节")):
            card = cls._research_steps(text)
        elif any(term in normalized for term in ("发表", "投稿", "录用")):
            card = cls._publication(text)
        elif any(term in normalized for term in ("责任", "独立", "共同", "指导下", "负责哪些任务", "具体负责")):
            card = cls._responsibilities(text)
        elif any(term in normalized for term in ("方法", "工具", "软件")):
            card = cls._methods_and_tools(text)
        elif any(term in normalized for term in ("结果", "产出", "材料", "形成")):
            card = cls._outputs(text)
        elif any(term in normalized for term in ("研究目标", "回答的问题")):
            card = cls._objective(text)
        elif any(term in normalized for term in ("质量控制", "复核", "一致性检查")):
            card = cls._quality_control(text)
        elif any(term in normalized for term in ("协作", "分工")):
            card = cls._collaboration(text)
        elif any(term in normalized for term in ("遇到过什么问题", "分歧", "如何处理")):
            card = cls._problem_solving(text)
        elif any(term in normalized for term in ("实际范围", "周期", "可确认数量")):
            card = cls._scope(text)
        else:
            card = cls._general_details(text)

        card["options"] = [*card["options"], cls._UNKNOWN]
        card.update({
            "text": text,
            "selection_mode": card.get("selection_mode", "multiple"),
            "allow_free_text": True,
            "allow_unknown": True,
        })
        return card

    @staticmethod
    def _clinical_setting(question: str) -> dict[str, Any]:
        return {
            "question_id": "clinical_setting",
            "why_it_matters": "科室、场景和病例类型决定这段经历的专业背景；可多选并补充真实科室。",
            "options": [
                _option("inpatient", "住院病区", "这段实践发生在住院病区。"),
                _option("outpatient", "门诊", "这段实践包含门诊场景。"),
                _option("emergency", "急诊", "这段实践包含急诊场景。"),
                _option("operating_room", "手术室", "这段实践包含手术室见习。"),
                _option("general_medicine", "内科", "我在内科相关科室实践。"),
                _option("surgery", "外科", "我在外科相关科室实践。"),
                _option("pediatrics", "儿科", "我在儿科相关科室实践。"),
                _option("obgyn", "妇产科", "我在妇产科相关科室实践。"),
            ],
        }

    @staticmethod
    def _clinical_tasks(question: str) -> dict[str, Any]:
        return {
            "question_id": "clinical_tasks",
            "why_it_matters": "临床实践要拆成可核实的具体环节，系统不会把见习自动写成独立诊疗。",
            "options": [
                _option("rounds", "参加查房", "我参加了临床查房。"),
                _option("history", "病史采集 / 问诊", "我参与病史采集或问诊。"),
                _option("exam", "体格检查", "我参与体格检查。"),
                _option("records", "查阅或整理病历", "我查阅或整理了病历资料。"),
                _option("case_discussion", "病例讨论", "我参与病例讨论。"),
                _option("documentation", "临床记录书写", "我参与临床记录书写。"),
                _option("communication", "患者沟通 / 宣教", "我参与患者沟通或健康宣教。"),
                _option("procedure", "观摩或协助临床操作", "我观摩或协助了临床操作。"),
                _option("handover", "交接班 / 病例交接", "我参与交接班或病例信息交接。"),
            ],
        }

    @staticmethod
    def _clinical_reasoning(question: str) -> dict[str, Any]:
        return {
            "question_id": "clinical_reasoning",
            "why_it_matters": "说明你如何整理临床信息，比笼统写“学习诊疗”更有证据；只选实际参与过的。",
            "options": [
                _option("problem_list", "梳理主诉、病史和问题清单", "我梳理了主诉、病史和临床问题清单。"),
                _option("findings", "分析检查或检验结果", "我参与分析检查或检验结果。"),
                _option("differential", "参与鉴别诊断讨论", "我参与鉴别诊断讨论。"),
                _option("plan", "参与诊疗思路讨论", "我参与诊疗思路讨论。"),
                _option("guideline", "围绕病例查阅指南", "我围绕具体病例查阅了临床指南。"),
                _option("presentation", "准备并汇报病例", "我准备并参与病例汇报。"),
            ],
        }

    @staticmethod
    def _clinical_outputs(question: str) -> dict[str, Any]:
        return {
            "question_id": "clinical_outputs",
            "why_it_matters": "真实形成的记录或汇报材料能证明临床学习过程，但不能替代执业权限。",
            "options": [
                _option("note", "病历或病程记录", "我形成了临床记录或病程记录。"),
                _option("case_summary", "病例总结", "我形成了病例总结。"),
                _option("presentation", "病例汇报 / PPT", "我形成了病例汇报材料或 PPT。"),
                _option("education", "患者宣教材料", "我参与形成患者宣教材料。"),
                _option("rotation_report", "轮转总结 / 出科汇报", "我形成了轮转总结或出科汇报。"),
                _option("none", "没有形成单独材料", "这段实践没有形成可单独列出的材料。"),
            ],
        }

    @staticmethod
    def _clinical_safety(question: str) -> dict[str, Any]:
        return {
            "question_id": "clinical_safety",
            "why_it_matters": "规范意识是临床经历的重要维度，但只能写实际遵循或执行过的环节。",
            "options": [
                _option("identity", "核对患者身份", "我按要求核对患者身份。"),
                _option("hand_hygiene", "手卫生", "我按要求执行手卫生规范。"),
                _option("infection", "感染防控", "我遵循了感染防控要求。"),
                _option("privacy", "患者隐私保护", "我遵循了患者隐私保护要求。"),
                _option("review", "记录提交带教复核", "我将临床记录提交带教老师复核。"),
                _option("scope", "不超出学生职责范围", "我在学生职责和带教要求范围内参与临床工作。"),
            ],
        }

    @staticmethod
    def _clinical_collaboration(question: str) -> dict[str, Any]:
        return {
            "question_id": "clinical_collaboration",
            "why_it_matters": "协作对象能说明临床工作如何发生，也有助于准确限定个人责任。",
            "options": [
                _option("attending", "带教 / 上级医师", "我与带教或上级医师协作。"),
                _option("resident", "住院医师", "我与住院医师协作。"),
                _option("nurse", "护理人员", "我与护理人员协作。"),
                _option("peers", "同组同学", "我与同组同学协作。"),
                _option("patient", "患者或家属", "我与患者或家属进行过沟通。"),
            ],
        }

    @staticmethod
    def _clinical_learning(question: str) -> dict[str, Any]:
        return {
            "question_id": "clinical_learning",
            "why_it_matters": "具体反馈与改进能体现学习能力，不需要编造成临床结果。",
            "options": [
                _option("history", "改进问诊顺序或完整性", "根据反馈，我改进了问诊顺序或信息完整性。"),
                _option("exam", "改进查体步骤或规范", "根据反馈，我改进了查体步骤或操作规范。"),
                _option("documentation", "改进记录结构和重点", "根据反馈，我改进了临床记录的结构和重点。"),
                _option("presentation", "改进病例汇报逻辑", "根据反馈，我改进了病例汇报逻辑。"),
                _option("communication", "改进沟通表达", "根据反馈，我改进了与患者或团队的沟通表达。"),
                _option("none", "没有可确认的具体反馈", "我目前不记得可确认的具体反馈。"),
            ],
        }

    @staticmethod
    def _databases(question: str) -> dict[str, Any]:
        return {
            "question_id": "databases_used",
            "why_it_matters": "数据库能证明检索范围和信息获取能力；只选择你实际使用过的。",
            "options": [
                _option("pubmed", "PubMed", "我使用了 PubMed。"),
                _option("embase", "Embase", "我使用了 Embase。"),
                _option("cochrane", "Cochrane Library", "我使用了 Cochrane Library。"),
                _option("web_of_science", "Web of Science", "我使用了 Web of Science。"),
                _option("cnki", "中国知网 CNKI", "我使用了中国知网 CNKI。"),
                _option("wanfang", "万方", "我使用了万方数据库。"),
                _option("vip", "维普", "我使用了维普数据库。"),
            ],
        }

    @staticmethod
    def _research_steps(question: str) -> dict[str, Any]:
        return {
            "question_id": "research_steps",
            "why_it_matters": "拆开具体步骤，才能判断每项工作的证据和责任边界。",
            "options": [
                _option("research_question", "明确研究问题", "我参与明确研究问题。"),
                _option("protocol", "制定或修改方案", "我参与制定或修改研究方案。"),
                _option("search_strategy", "设计检索式", "我参与设计检索式。"),
                _option("literature_search", "执行文献检索", "我执行了文献检索。"),
                _option("screening", "文献筛选", "我参与文献筛选。"),
                _option("data_extraction", "数据提取", "我参与数据提取。"),
                _option("quality_assessment", "质量评价 / 偏倚评估", "我参与质量评价或偏倚评估。"),
                _option("statistical_analysis", "统计分析", "我参与统计分析。"),
                _option("sensitivity", "敏感性 / 亚组分析", "我参与敏感性分析或亚组分析。"),
                _option("writing", "论文或汇报材料撰写", "我参与论文或汇报材料撰写。"),
            ],
        }

    @staticmethod
    def _publication(question: str) -> dict[str, Any]:
        return {
            "question_id": "publication_status",
            "selection_mode": "single",
            "why_it_matters": "发表状态必须准确，不能把计划或投稿写成已发表。",
            "options": [
                _option("no_plan", "暂无发表计划", "该项目目前没有明确发表计划。"),
                _option("preparing", "正在整理材料", "该项目正在整理论文材料。"),
                _option("submitted", "已经投稿", "该项目已经投稿。"),
                _option("under_review", "审稿中", "该项目目前处于审稿阶段。"),
                _option("accepted", "已录用", "该项目相关论文已录用。"),
                _option("published", "已发表", "该项目相关论文已发表。"),
            ],
        }

    @staticmethod
    def _responsibilities(question: str) -> dict[str, Any]:
        return {
            "question_id": "responsibility_boundary",
            "why_it_matters": "简历强度取决于你实际负责的范围，协助、负责模块和主导不能混用。",
            "options": [
                _option("supervised", "在指导下完成", "相关工作是在指导下完成的。"),
                _option("shared", "与他人共同完成", "相关工作是与团队成员共同完成的。"),
                _option("independent", "独立完成", "相关工作由我独立完成。"),
                _option("contributed", "参与 / 协助", "我参与或协助完成相关工作。"),
                _option("owned_component", "负责明确模块", "我负责其中一个明确模块。"),
                _option("partial", "只覆盖部分步骤", "我只完成了其中部分步骤。"),
                _option("full", "覆盖完整流程", "我完成了该活动的完整流程。"),
                _option("coordinated", "负责协调推进", "我负责协调相关任务推进，但不是项目最终责任人。"),
            ],
        }

    @staticmethod
    def _methods_and_tools(question: str) -> dict[str, Any]:
        return {
            "question_id": "methods_and_tools",
            "why_it_matters": "方法和工具只有与你实际执行的任务关联时才进入简历。",
            "options": [
                _option("systematic_review", "系统综述", "我使用了系统综述方法。"),
                _option("meta_analysis", "Meta 分析", "我使用了 Meta 分析方法。"),
                _option("mr", "孟德尔随机化", "我使用了孟德尔随机化方法。"),
                _option("sensitivity", "敏感性分析", "我使用了敏感性分析。"),
                _option("stata", "Stata", "我使用了 Stata。"),
                _option("r", "R", "我使用了 R。"),
                _option("spss", "SPSS", "我使用了 SPSS。"),
                _option("revman", "RevMan", "我使用了 RevMan。"),
                _option("excel", "Excel", "我使用了 Excel。"),
                _option("python", "Python", "我使用了 Python。"),
            ],
        }

    @staticmethod
    def _outputs(question: str) -> dict[str, Any]:
        return {
            "question_id": "outputs",
            "why_it_matters": "可复核的材料比笼统的“参与项目”更能证明工作内容。",
            "options": [
                _option("search_record", "检索式 / 检索记录", "我形成了检索式或检索记录。"),
                _option("screening_record", "筛选记录", "我形成了文献筛选记录。"),
                _option("extraction_sheet", "数据提取表", "我形成了数据提取表。"),
                _option("analysis_code", "分析代码", "我形成了可复核的分析代码。"),
                _option("analysis_tables", "分析图表", "我形成了分析图表。"),
                _option("report", "研究报告 / 汇报材料", "我形成了研究报告或汇报材料。"),
                _option("manuscript", "论文材料", "我参与形成论文材料。"),
                _option("sop", "SOP / 流程文件", "我参与形成 SOP 或流程文件。"),
            ],
        }

    @staticmethod
    def _objective(question: str) -> dict[str, Any]:
        return {
            "question_id": "objective",
            "why_it_matters": "明确目标能让简历说明这项工作为什么开展，而不只是罗列操作。",
            "options": [
                _option("association", "探索因素与结局的关系", "这项工作的研究目标是探索因素与结局的关系。"),
                _option("intervention", "评估干预或方案效果", "这项工作的研究目标是评估干预或方案效果。"),
                _option("comparison", "比较不同方法或人群", "这项工作的研究目标是比较不同方法或人群。"),
                _option("description", "描述疾病或样本特征", "这项工作的研究目标是描述疾病或样本特征。"),
                _option("model", "建立或验证模型", "这项工作的研究目标是建立或验证模型。"),
                _option("evidence", "总结现有证据", "这项工作的研究目标是总结现有证据。"),
            ],
        }

    @staticmethod
    def _quality_control(question: str) -> dict[str, Any]:
        return {
            "question_id": "quality_control",
            "why_it_matters": "质量控制能证明工作可靠性，但只能选择实际做过的步骤。",
            "options": [
                _option("double_review", "双人独立处理或交叉复核", "我与团队成员进行了交叉复核。"),
                _option("source_check", "回查原文或原始数据", "我通过回查原文或核对原始数据进行质量复核。"),
                _option("criteria_check", "按标准核对纳入或排除", "我按标准核对纳入排除结果。"),
                _option("bias_assessment", "质量评价或偏倚评估", "我参与质量评价或偏倚评估。"),
                _option("repeat_analysis", "重复分析或敏感性检查", "我进行了重复分析或敏感性分析。"),
                _option("team_review", "提交导师或团队复核", "我将阶段结果提交导师或团队复核。"),
            ],
        }

    @staticmethod
    def _collaboration(question: str) -> dict[str, Any]:
        return {
            "question_id": "collaboration",
            "why_it_matters": "说明分工有助于区分个人贡献和团队成果。",
            "options": [
                _option("supervisor", "与导师协作", "这项工作与导师协作完成。"),
                _option("peer", "与同学或课题组成员协作", "这项工作与同学或课题组成员协作完成。"),
                _option("clinician", "与临床医生协作", "这项工作与临床医生协作完成。"),
                _option("statistician", "与统计或数据人员协作", "这项工作与统计或数据人员协作完成。"),
                _option("independent", "该任务主要由我独立完成", "这项任务主要由我独立完成。"),
            ],
        }

    @staticmethod
    def _problem_solving(question: str) -> dict[str, Any]:
        return {
            "question_id": "problem_solving",
            "why_it_matters": "具体问题与处理方式比笼统的“能力强”更有说服力。",
            "options": [
                _option("disagreement", "处理筛选、判断或记录分歧", "我参与处理筛选、判断或记录分歧。"),
                _option("data_issue", "核查并修正数据问题", "我核查并修正了数据问题。"),
                _option("search_issue", "调整检索或资料获取方式", "我根据问题调整了检索或资料获取方式。"),
                _option("analysis_issue", "排查分析或代码问题", "我排查并处理了分析或代码问题。"),
                _option("experiment_issue", "优化实验条件或操作", "我参与优化实验条件或操作。"),
                _option("none", "没有需要特别说明的问题", "过程中没有需要特别说明的问题或分歧。"),
            ],
        }

    @staticmethod
    def _scope(question: str) -> dict[str, Any]:
        return {
            "question_id": "scope",
            "why_it_matters": "范围和周期能增强具体性；不记得数字时可以只说明完整或部分范围。",
            "options": [
                _option("full", "完成完整流程", "这项任务覆盖完整流程。"),
                _option("partial", "完成其中部分步骤", "这项任务只覆盖部分步骤。"),
                _option("ongoing", "目前仍在进行", "这项任务目前仍在进行。"),
                _option("remember_period", "记得大致周期，可补充"),
                _option("remember_count", "记得确切数量，可补充"),
            ],
        }

    @staticmethod
    def _general_details(question: str) -> dict[str, Any]:
        return {
            "question_id": "experience_details",
            "why_it_matters": "可以先选择接近的方向，再在文本框里补充真实细节。",
            "options": [
                _option("steps", "补充具体步骤", "我想补充实际执行的具体步骤。"),
                _option("methods", "补充方法或工具", "我想补充实际使用的方法或工具。"),
                _option("responsibility", "补充责任边界", "我想补充本人实际负责的范围。"),
                _option("output", "补充产出材料", "我想补充实际形成的材料或结果。"),
                _option("scale", "补充数量或周期", "我想补充可核实的数量或时间周期。"),
                _option("collaboration", "补充协作对象", "我想补充实际协作对象和分工。"),
            ],
        }
