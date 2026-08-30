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
        if any(term in normalized for term in ("数据库", "文献检索")):
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
