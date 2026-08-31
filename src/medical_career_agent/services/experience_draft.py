from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Sequence

from ..adapters.openai_compatible_model_gateway import ModelGatewayError


@dataclass(frozen=True)
class ExperienceDraft:
    """Draft experience record with extracted facts and guidance."""

    extracted_facts: dict[str, Any]
    unknown_items: list[str]
    possible_value_angles: list[str]
    clarifying_questions: list[str]
    all_clarifying_questions: list[str]
    risk_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "extracted_facts": self.extracted_facts,
            "unknown_items": self.unknown_items,
            "possible_value_angles": self.possible_value_angles,
            "clarifying_questions": self.clarifying_questions,
            "all_clarifying_questions": self.all_clarifying_questions,
            "risk_flags": self.risk_flags,
        }


class ExperienceDraftService:
    """Extracts facts from user's raw experience text and provides guidance."""

    # Medical research action patterns
    ACTION_PATTERNS = {
        "define_research_question": [
            r"明确研究问题", r"提出研究问题", r"定义研究问题",
        ],
        "develop_protocol": [
            r"制定(?:或修改)?研究方案", r"修改研究方案", r"研究方案制定",
            r"develop(?:ed)? protocol", r"study protocol",
        ],
        "design_search_strategy": [
            r"设计检索式", r"制定检索策略", r"检索策略",
            r"search strateg(?:y|ies)",
        ],
        "retrieve_literature": [
            r"文献检索", r"检索文献", r"查找文献", r"搜索文献",
            r"literature search", r"search literature", r"find papers"
        ],
        "screen_studies": [
            r"筛选", r"筛选文献", r"文献筛选", r"纳入排除",
            r"screen", r"screening", r"inclusion exclusion"
        ],
        "extract_data": [
            r"数据提取", r"提取数据", r"数据抽取",
            r"data extraction", r"extract data"
        ],
        "create_flowchart": [
            r"流程图", r"PRISMA流程图", r"绘制流程图",
            r"flowchart", r"PRISMA flowchart"
        ],
        "assess_quality": [
            r"质量评价", r"偏倚评估", r"偏倚风险评估",
            r"quality assessment", r"risk of bias",
        ],
        "verify_research_quality": [
            r"交叉复核", r"回查原文", r"核对原始数据", r"一致性检查",
            r"核对(?:纳入|排除|提取)", r"提交.*(?:导师|团队).*复核",
        ],
        "resolve_workflow_issue": [
            r"处理.*(?:分歧|异常|问题)", r"核查.*修正", r"调整检索",
            r"排查.*(?:分析|代码)", r"优化实验条件",
        ],
        "prepare_research_outputs": [
            r"(?:形成|整理|制作).*(?:检索记录|筛选记录|数据提取表|分析代码|分析图表|研究报告|论文材料|SOP|流程文件)",
            r"prepare.*(?:report|record|table|code|figure|manuscript|SOP)",
        ],
        "perform_analysis": [
            r"统计分析", r"数据分析", r"敏感性分析", r"进行分析", r"R\s*分析", r"跑数据",
            r"(?:用|使用)\s*R.*完成.*[Mm]eta\s*分析",
            r"analyze", r"statistical analysis", r"data analysis"
        ],
        "write_manuscript": [
            r"撰写", r"写作", r"写论文", r"撰写论文",
            r"write", r"manuscript", r"paper writing"
        ],
        "culture_cells": [r"细胞培养", r"cell culture"],
        "perform_qpcr": [r"qPCR", r"RT[- ]?qPCR", r"实时定量PCR"],
        "perform_western_blot": [r"Western[ -]?Blot", r"蛋白印迹"],
        "review_clinical_case": [
            r"病例汇报", r"病例讨论", r"病例分析", r"病例总结",
            r"鉴别诊断讨论", r"诊疗思路讨论", r"临床问题清单", r"case presentation",
        ],
        "prepare_case_presentation": [r"病例汇报材料", r"准备.*病例汇报.*PPT", r"准备.*PPT", r"制作.*PPT", r"现场汇报", r"presentation"],
        "retrieve_guidelines": [r"查阅指南", r"临床指南", r"诊疗指南", r"guideline"],
        "join_ward_rounds": [r"查房", r"ward rounds?"],
        "collect_medical_history": [r"病史采集", r"询问病史", r"问诊", r"history taking"],
        "perform_physical_examination": [r"体格检查", r"查体", r"physical examination"],
        "review_patient_records": [r"查阅病历", r"病历资料", r"病历整理", r"review.*(?:chart|record)"],
        "interpret_clinical_findings": [r"分析.*(?:检查|检验|影像|心电图|化验)", r"解读.*(?:检查|检验|影像|心电图|化验)", r"检查结果", r"检验结果"],
        "document_clinical_work": [r"书写病历", r"临床记录(?:书写)?", r"病程记录", r"入院记录", r"出院记录", r"clinical documentation"],
        "communicate_with_patients": [r"患者沟通", r"病情沟通", r"健康宣教", r"患者教育", r"patient communication"],
        "support_clinical_procedure": [r"观摩.*操作", r"协助.*操作", r"参与.*操作", r"操作见习", r"procedure"],
        "handover_clinical_information": [r"交接班", r"病例交接", r"handover"],
        "follow_clinical_safety": [r"手卫生", r"感染防控", r"隐私保护", r"核对患者身份", r"医疗安全"],
        "collaborate_clinical_team": [r"与.*(?:医师|护理人员|护士|同组同学).*协作", r"临床团队协作"],
        "incorporate_clinical_feedback": [r"根据反馈.*改进", r"带教反馈", r"纠正.*(?:问诊|查体|记录|汇报|沟通)"],
    }

    # Experimental techniques are distinct from research methods and software tools.
    TECHNIQUE_PATTERNS = {
        "cell_culture": [r"细胞培养", r"cell culture"],
        "qpcr": [r"qPCR", r"RT[- ]?qPCR", r"实时定量PCR"],
        "western_blot": [r"Western[ -]?Blot", r"蛋白印迹"],
        "flow_cytometry": [r"流式细胞", r"flow cytometry"],
        "elisa": [r"ELISA", r"酶联免疫"],
        "animal_experiment": [r"动物实验", r"animal study"],
    }

    # Medical research method patterns
    METHOD_PATTERNS = {
        "systematic_review": [
            r"系统综述", r"系统评价", r"systematic review"
        ],
        "meta_analysis": [
            r"Meta\s*分析", r"荟萃分析", r"meta[- ]?analysis"
        ],
        "randomized_trial": [
            r"随机对照试验", r"RCT", r"randomized trial", r"RCT"
        ],
        "cohort_study": [
            r"队列研究", r"cohort study"
        ],
        "case_control": [
            r"病例对照", r"case[- ]?control"
        ],
        "mendelian_randomization": [
            r"孟德尔随机化", r"\bMR\b", r"mendelian randomization"
        ],
        "sensitivity_analysis": [
            r"敏感性分析", r"sensitivity analysis"
        ],
    }

    TOOL_PATTERNS = (
        (r"SPSS", "spss"),
        (r"R语言|R[- ]?script|(?<![A-Za-z])R(?![A-Za-z])", "r"),
        (r"Python", "python"),
        (r"SQL", "sql"),
        (r"Stata", "stata"),
        (r"SAS", "sas"),
        (r"Excel", "excel"),
        (r"RevMan", "revman"),
        (r"EndNote", "endnote"),
        (r"NoteExpress", "noteexpress"),
        (r"PubMed", "pubmed"),
        (r"Embase", "embase"),
        (r"Cochrane", "cochrane"),
        (r"Web of Science", "web_of_science"),
        (r"中国知网|CNKI", "cnki"),
        (r"万方", "wanfang"),
        (r"维普", "vip"),
        (r"GraphPad(?: Prism)?", "graphpad_prism"),
    )

    COLLABORATION_PATTERNS = {
        "research_team": (r"课题组", r"team", r"group"),
        "supervisor": (r"导师", r"supervisor"),
        "peer": (r"同学", r"团队成员"),
        "clinician": (r"临床医生",),
        "attending_physician": (r"带教(?:老师|医师)?", r"上级医师", r"住院医师"),
        "nurse": (r"护理人员", r"护士"),
        "patient_or_family": (r"患者或家属", r"患者沟通", r"病情沟通", r"健康宣教"),
        "statistician": (r"统计人员", r"数据人员"),
    }

    ARTIFACT_PATTERNS = {
        "prisma_flowchart": (r"流程图", r"flowchart"),
        "search_record": (r"检索式", r"检索记录", r"search strateg", r"search record"),
        "screening_record": (r"筛选记录", r"screening record"),
        "data_extraction_sheet": (r"数据表", r"数据提取表", r"data sheet", r"extraction sheet"),
        "analysis_code": (r"分析代码", r"统计代码", r"analysis code", r"analysis script"),
        "research_paper": (r"论文", r"paper", r"manuscript"),
        "analysis_figures": (r"结果图表", r"森林图", r"图表"),
        "research_report": (r"研究报告", r"汇报材料", r"research report"),
        "sop": (r"SOP", r"流程文件", r"standard operating procedure"),
        "group_presentation": (r"组会汇报", r"组会讨论"),
        "case_presentation_material": (r"病例汇报材料", r"准备.*PPT", r"制作.*PPT", r"现场汇报"),
        "clinical_note": (r"病历记录", r"病程记录", r"入院记录", r"出院记录", r"书写病历"),
        "case_summary": (r"病例总结", r"病例整理", r"病例汇报"),
        "patient_education_material": (r"宣教材料", r"患者教育材料"),
        "rotation_report": (r"轮转总结", r"出科汇报", r"实习总结"),
    }

    def draft(
        self,
        *,
        experience_text: str,
        context_hint: str | None = None,
        experience_type: str | None = None,
        consent_confirmed: bool = False,
    ) -> ExperienceDraft:
        """Create a draft experience record from raw text."""
        if not experience_text.strip():
            raise ValueError("experience_text cannot be empty")
        if not consent_confirmed:
            raise ValueError("consent_confirmed must be True")

        # Extract facts using deterministic rules first
        extracted_facts = self._extract_facts_deterministic(
            experience_text, context_hint, experience_type,
        )
        unknown_items = self._identify_unknowns(
            extracted_facts, experience_text, experience_type,
        )
        possible_value_angles = self._generate_value_angles(extracted_facts)
        clarifying_questions = self._generate_clarifying_questions(
            extracted_facts, unknown_items, experience_type,
        )
        risk_flags = self._identify_risk_flags(extracted_facts, experience_text)

        return ExperienceDraft(
            extracted_facts=extracted_facts,
            unknown_items=unknown_items,
            possible_value_angles=possible_value_angles,
            clarifying_questions=clarifying_questions[:3],
            all_clarifying_questions=clarifying_questions[:8],
            risk_flags=risk_flags,
        )

    def _extract_facts_deterministic(
        self,
        text: str,
        context_hint: str | None = None,
        experience_type: str | None = None,
    ) -> dict[str, Any]:
        """Extract facts using deterministic pattern matching."""
        facts = {
            "context": self._extract_context(text, context_hint, experience_type),
            "role": self._extract_role(text),
            "actions": self._extract_actions(text),
            "methods": self._extract_methods(text),
            "tools": self._extract_tools(text),
            "techniques": self._extract_techniques(text),
            "objects": self._extract_objects(text),
            "collaboration": self._extract_collaboration(text),
            "artifacts": self._extract_artifacts(text),
            "outcomes": self._extract_outcomes(text),
            "scope": self._extract_scope(text),
        }
        return facts

    def _extract_context(
        self, text: str, context_hint: str | None, experience_type: str | None = None,
    ) -> dict[str, str | None]:
        """Extract context domain and setting."""
        domain = "clinical_research"  # Default domain
        setting = "research_project"   # Default setting

        if experience_type == "clinical":
            domain, setting = "clinical_practice", "clinical_rotation"

        # Check for domain patterns in order of specificity.  An explicit UI
        # type wins: clinical practice must not silently become research.
        domain_patterns = [
            ("clinical_research", [r"临床研究", r"临床试验", r"病例汇报", r"病例讨论", r"clinical research", r"clinical trial", r"Meta分析", r"meta[- ]?analysis", r"系统综述"]),
            ("wet_lab", [r"实验", r"实验室", r"细胞培养", r"qPCR", r"Western[ -]?Blot", r"lab", r"wet lab", r"分子实验"]),
            ("data_analysis", [r"数据分析", r"统计分析", r"data analysis", r"statistical analysis"]),
            ("medical_information", [r"文献", r"医学信息", r"medical information", r"literature"])
        ]

        if experience_type != "clinical":
            for candidate_domain, patterns in domain_patterns:
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    domain = candidate_domain
                    break

        # Check for setting patterns
        setting_patterns = [
            ("clinical_trial", [r"临床试验", r"clinical trial"]),
            ("research_project", [r"课题组", r"项目", r"project", r"课题", r"研究项目"]),
            ("lab_experiment", [r"实验室", r"lab", r"实验"]),
            ("data_project", [r"数据分析项目", r"data project"])
        ]

        if experience_type != "clinical":
            for candidate_setting, patterns in setting_patterns:
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    setting = candidate_setting
                    break

        # Use context hint if provided and no patterns matched
        if context_hint and domain == "clinical_research" and setting == "research_project":
            hint_lower = context_hint.lower()
            if "临床" in hint_lower or "clinical" in hint_lower:
                domain = "clinical_research"
            elif "实验" in hint_lower or "lab" in hint_lower:
                domain = "wet_lab"
            elif "数据" in hint_lower or "data" in hint_lower:
                domain = "data_analysis"

        topic_match = re.search(
            r"(?:研究目的|研究目标)(?:是|为|：|:)?\s*([^。；;\n]{2,120})",
            text,
            re.IGNORECASE,
        )
        return {
            "domain": domain,
            "setting": setting,
            "topic": topic_match.group(1).strip() if topic_match else None,
        }

    def _extract_role(self, text: str) -> dict[str, str | None]:
        """Extract role responsibility level."""
        # Default to participated (most conservative)
        responsibility_level = "participated"
        title = None

        # Check for higher responsibility indicators
        if re.search(r"负责|主导|lead|manage|own", text, re.IGNORECASE):
            # But don't automatically upgrade - this should be confirmed by user
            responsibility_level = "participated"  # Keep conservative

        # Look for specific role titles
        title_match = re.search(r"(?:担任|作为|role as)\s*([^\s,，.。]+)", text, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

        return {
            "title": title,
            "responsibility_level": responsibility_level
        }

    def _extract_actions(self, text: str) -> list[str]:
        """Extract actions using pattern matching."""
        actions = []
        for action, patterns in self.ACTION_PATTERNS.items():
            # A phrase such as "PubMed 检索文献技能" describes a capability,
            # not necessarily a completed retrieval activity in this experience.
            if action == "retrieve_literature" and re.search(r"(?:检索文献|文献检索)技能", text, re.IGNORECASE):
                continue
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                actions.append(action)
        return actions

    def _extract_methods(self, text: str) -> list[str]:
        """Extract methods using pattern matching."""
        methods = []
        for method, patterns in self.METHOD_PATTERNS.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                methods.append(method)
        return methods

    def _extract_techniques(self, text: str) -> list[str]:
        """Extract laboratory techniques without treating them as research methods."""
        techniques = []
        for technique, patterns in self.TECHNIQUE_PATTERNS.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                techniques.append(technique)
        return techniques

    def _extract_tools(self, text: str) -> list[str]:
        """Extract tools (software, equipment, etc.)."""
        tools = []
        for pattern, tool_name in self.TOOL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                tools.append(tool_name)
        return tools

    def _extract_objects(self, text: str) -> list[str]:
        """Extract objects (what the actions are performed on)."""
        objects = []
        if re.search(r"文献|papers|studies|articles", text, re.IGNORECASE):
            objects.append("medical_literature")
        if re.search(r"临床研究|临床试验|clinical (research|trial|studies)", text, re.IGNORECASE):
            objects.append("clinical_studies")
        if re.search(r"数据|data", text, re.IGNORECASE):
            objects.append("research_data")
        if re.search(r"病例", text, re.IGNORECASE):
            objects.append("clinical_case")
        if re.search(r"患者|病人|病历|问诊|查房", text, re.IGNORECASE):
            objects.append("patient_records")
        if re.search(r"细胞|RNA|蛋白", text, re.IGNORECASE):
            objects.append("laboratory_samples")
        return objects

    def _extract_collaboration(self, text: str) -> list[str]:
        """Extract collaboration information."""
        return [
            item_id for item_id, patterns in self.COLLABORATION_PATTERNS.items()
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
        ]

    def _extract_artifacts(self, text: str) -> list[str]:
        """Extract artifacts (deliverables, outputs)."""
        return [
            item_id for item_id, patterns in self.ARTIFACT_PATTERNS.items()
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
        ]

    def _extract_outcomes(self, text: str) -> list[str]:
        """Extract outcomes (results, achievements)."""
        statuses = (
            ("no_publication_plan", (r"暂无发表计划", r"没有发表计划", r"未计划发表")),
            ("materials_preparing", (r"正在整理(?:论文)?材料", r"论文材料整理")),
            ("submitted", (r"已经投稿", r"已投稿")),
            ("under_review", (r"审稿中", r"under review")),
            ("accepted", (r"已录用", r"accepted")),
            ("published", (r"已发表", r"published")),
        )
        return [
            status for status, patterns in statuses
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
        ]

    def _extract_scope(self, text: str) -> dict[str, str]:
        """Extract scope information (numbers, ranges, etc.)."""
        # Don't extract scope deterministically to avoid guessing numbers
        return {}

    def _identify_unknowns(
        self, facts: dict[str, Any], text: str, experience_type: str | None = None,
    ) -> list[str]:
        """Identify unknown items that would improve the expression."""
        unknowns = []

        if experience_type == "clinical":
            if not re.search(r"科|病区|门诊|急诊|轮转|见习|实习", text):
                unknowns.append("clinical_setting")
            if not facts["actions"]:
                unknowns.append("clinical_tasks")
            if not any(action in facts["actions"] for action in (
                "review_clinical_case", "interpret_clinical_findings", "retrieve_guidelines",
            )):
                unknowns.append("clinical_reasoning")
            if not facts["artifacts"]:
                unknowns.append("clinical_outputs")
            if not re.search(r"指导|带教|上级医师|独立|共同|协助|观摩", text):
                unknowns.append("specific_responsibilities")
            if not re.search(r"手卫生|感染防控|隐私|核对|安全|规范", text):
                unknowns.append("clinical_safety")
            if not facts["collaboration"] and not re.search(r"医师|护士|患者|家属|团队|同学", text):
                unknowns.append("clinical_collaboration")
            if not re.search(r"反馈|改进|困难|问题|调整|纠正", text):
                unknowns.append("clinical_learning")
            return unknowns

        # If actions include literature retrieval, ask about databases
        database_tools = {
            "pubmed", "embase", "cochrane", "web_of_science", "cnki", "wanfang", "vip",
        }
        if "retrieve_literature" in facts["actions"] and not database_tools.intersection(facts["tools"]):
            unknowns.append("databases_used")

        # If methods include meta_analysis, ask about the workflow rather than
        # requiring a remembered study count.
        if "meta_analysis" in facts["methods"]:
            unknowns.append("screening_criteria")

        # If no outcomes are specified, ask about results
        if not facts["outcomes"] and not re.search(r"没有发表|未发表|尚未发表", text, re.IGNORECASE):
            unknowns.append("publication_status")

        if not facts["artifacts"]:
            unknowns.append("deliverables")

        # If responsibility is unclear, ask for clarification
        if facts["role"]["responsibility_level"] == "participated":
            unknowns.append("specific_responsibilities")

        if not re.search(r"研究目的|研究目标|旨在|探讨|评估|比较|验证|分析.*关系", text, re.IGNORECASE):
            unknowns.append("objective")
        if not re.search(r"复核|核对|回查|质控|质量控制|一致性|偏倚|重复分析|双人", text, re.IGNORECASE):
            unknowns.append("quality_control")
        if not facts["collaboration"] and not re.search(r"共同|协作|分工|沟通|讨论", text, re.IGNORECASE):
            unknowns.append("collaboration")
        if not re.search(r"解决|排查|调整|修正|处理.*(?:问题|分歧|异常)|优化", text, re.IGNORECASE):
            unknowns.append("problem_solving")
        if not re.search(r"\d+|完整流程|部分步骤|持续|周期|范围", text, re.IGNORECASE):
            unknowns.append("scope")

        return unknowns

    def _generate_value_angles(self, facts: dict[str, Any]) -> list[str]:
        """Generate possible value angles for different roles."""
        value_angles = []

        # Based on extracted facts, suggest potential values
        if "meta_analysis" in facts["methods"]:
            value_angles.append("该经历可能体现循证研究方法掌握能力")
            value_angles.append("可展现系统性文献检索与证据综合能力")

        if "retrieve_literature" in facts["actions"]:
            value_angles.append("文献检索能力在MSL岗位中非常重要")
            value_angles.append("系统性检索能力体现科研训练基础")

        if "clinical_research" == facts["context"]["domain"]:
            value_angles.append("临床研究经验对考博和临床科研岗位都很有价值")
            value_angles.append("可展现医学问题理解和研究执行能力")

        return value_angles[:3]  # Limit to 3 value angles

    def _generate_clarifying_questions(
        self, facts: dict[str, Any], unknowns: list[str], experience_type: str | None = None,
    ) -> list[str]:
        """Generate clarifying questions to improve the expression."""
        questions = []

        if experience_type == "clinical":
            clinical_questions = {
                "clinical_setting": "这段临床实践发生在哪个科室或场景，主要接触哪类病例？",
                "clinical_tasks": "你在临床实践中实际参与了哪些环节？",
                "clinical_reasoning": "你参与过哪些病例分析、检查结果解读或指南查阅？",
                "specific_responsibilities": "这些临床任务中，哪些是观摩、协助、在带教下完成或可独立完成？",
                "clinical_outputs": "你实际形成或完成过哪些临床记录、病例总结或汇报材料？",
                "clinical_safety": "你实际遵循过哪些医疗安全、感染防控或隐私规范？",
                "clinical_collaboration": "你在临床实践中与哪些人员协作或沟通？",
                "clinical_learning": "带教反馈或实际问题让你改进了哪项具体做法？",
            }
            return [clinical_questions[item] for item in unknowns if item in clinical_questions]

        # Prioritize questions that would most impact resume expression
        if "databases_used" in unknowns:
            questions.append("使用了哪些数据库进行文献检索？")

        if "screening_criteria" in unknowns:
            questions.append("你负责了文献筛选、数据提取或质量评价中的哪些环节？")

        if "specific_responsibilities" in unknowns:
            questions.append("你在项目中具体负责哪些任务？")

        if "deliverables" in unknowns:
            questions.append("你实际形成了哪些可复核的材料或结果？")

        if "publication_status" in unknowns:
            questions.append("这个项目是否有发表计划或已发表？")

        if "objective" in unknowns:
            questions.append("这项工作的研究目标或希望回答的问题是什么？")
        if "quality_control" in unknowns:
            questions.append("你在执行过程中做过哪些质量控制、复核或一致性检查？")
        if "collaboration" in unknowns:
            questions.append("这项工作与谁协作，你和其他人的分工是什么？")
        if "problem_solving" in unknowns:
            questions.append("过程中遇到过什么问题或分歧，你具体如何处理？")
        if "scope" in unknowns:
            questions.append("这项任务的实际范围、周期或可确认数量是什么？")

        return questions

    def _identify_risk_flags(self, facts: dict[str, Any], text: str) -> list[str]:
        """Identify potential risks in the input text."""
        risk_flags = []

        # Check for potential responsibility upgrade
        if re.search(r"负责|主导", text, re.IGNORECASE) and facts["role"]["responsibility_level"] == "participated":
            risk_flags.append("可能存在责任等级升级风险")

        # Check for potential number fabrication
        if re.search(r"\d+", text) and not facts["scope"]:
            risk_flags.append("包含数字但未确认具体含义")

        # Check for vague descriptions
        if len(text.strip()) < 20:
            risk_flags.append("描述过于简短，可能遗漏重要细节")

        return risk_flags
