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
    risk_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "extracted_facts": self.extracted_facts,
            "unknown_items": self.unknown_items,
            "possible_value_angles": self.possible_value_angles,
            "clarifying_questions": self.clarifying_questions,
            "risk_flags": self.risk_flags,
        }


class ExperienceDraftService:
    """Extracts facts from user's raw experience text and provides guidance."""

    # Medical research action patterns
    ACTION_PATTERNS = {
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
        "perform_analysis": [
            r"分析", r"统计分析", r"数据分析", r"进行分析",
            r"analyze", r"statistical analysis", r"data analysis"
        ],
        "write_manuscript": [
            r"撰写", r"写作", r"写论文", r"撰写论文",
            r"write", r"manuscript", r"paper writing"
        ],
        "culture_cells": [r"细胞培养", r"cell culture"],
        "perform_qpcr": [r"qPCR", r"RT[- ]?qPCR", r"实时定量PCR"],
        "perform_western_blot": [r"Western[ -]?Blot", r"蛋白印迹"],
        "review_clinical_case": [r"病例汇报", r"病例讨论", r"病例分析", r"case presentation"],
        "prepare_case_presentation": [r"病例汇报材料", r"制作.*PPT", r"现场汇报", r"presentation"],
        "retrieve_guidelines": [r"查阅指南", r"临床指南", r"guideline"]
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
    }

    def draft(
        self,
        *,
        experience_text: str,
        context_hint: str | None = None,
        consent_confirmed: bool = False,
    ) -> ExperienceDraft:
        """Create a draft experience record from raw text."""
        if not experience_text.strip():
            raise ValueError("experience_text cannot be empty")
        if not consent_confirmed:
            raise ValueError("consent_confirmed must be True")

        # Extract facts using deterministic rules first
        extracted_facts = self._extract_facts_deterministic(experience_text, context_hint)
        unknown_items = self._identify_unknowns(extracted_facts, experience_text)
        possible_value_angles = self._generate_value_angles(extracted_facts)
        clarifying_questions = self._generate_clarifying_questions(extracted_facts, unknown_items)
        risk_flags = self._identify_risk_flags(extracted_facts, experience_text)

        return ExperienceDraft(
            extracted_facts=extracted_facts,
            unknown_items=unknown_items,
            possible_value_angles=possible_value_angles,
            clarifying_questions=clarifying_questions[:3],  # Limit to 3 questions
            risk_flags=risk_flags,
        )

    def _extract_facts_deterministic(
        self,
        text: str,
        context_hint: str | None = None
    ) -> dict[str, Any]:
        """Extract facts using deterministic pattern matching."""
        facts = {
            "context": self._extract_context(text, context_hint),
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

    def _extract_context(self, text: str, context_hint: str | None) -> dict[str, str | None]:
        """Extract context domain and setting."""
        domain = "clinical_research"  # Default domain
        setting = "research_project"   # Default setting

        # Check for domain patterns in order of specificity
        domain_patterns = [
            ("clinical_research", [r"临床研究", r"临床试验", r"病例汇报", r"病例讨论", r"clinical research", r"clinical trial", r"Meta分析", r"meta[- ]?analysis", r"系统综述"]),
            ("wet_lab", [r"实验", r"实验室", r"细胞培养", r"qPCR", r"Western[ -]?Blot", r"lab", r"wet lab", r"分子实验"]),
            ("data_analysis", [r"数据分析", r"统计分析", r"data analysis", r"statistical analysis"]),
            ("medical_information", [r"文献", r"医学信息", r"medical information", r"literature"])
        ]

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

        return {
            "domain": domain,
            "setting": setting,
            "topic": None  # Topic requires more sophisticated extraction
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
        # Common medical research tools
        tool_patterns = [
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
            (r"GraphPad(?: Prism)?", "graphpad_prism"),
        ]
        for pattern, tool_name in tool_patterns:
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
        if re.search(r"细胞|RNA|蛋白", text, re.IGNORECASE):
            objects.append("laboratory_samples")
        return objects

    def _extract_collaboration(self, text: str) -> list[str]:
        """Extract collaboration information."""
        collaboration = []
        if re.search(r"课题组|team|group", text, re.IGNORECASE):
            collaboration.append("research_team")
        if re.search(r"导师|supervisor", text, re.IGNORECASE):
            collaboration.append("supervisor")
        return collaboration

    def _extract_artifacts(self, text: str) -> list[str]:
        """Extract artifacts (deliverables, outputs)."""
        artifacts = []
        if re.search(r"流程图|flowchart", text, re.IGNORECASE):
            artifacts.append("prisma_flowchart")
        if re.search(r"数据表|data sheet", text, re.IGNORECASE):
            artifacts.append("data_extraction_sheet")
        if re.search(r"论文|paper|manuscript", text, re.IGNORECASE):
            artifacts.append("research_paper")
        if re.search(r"病例汇报材料|制作.*PPT|现场汇报", text, re.IGNORECASE):
            artifacts.append("case_presentation_material")
        return artifacts

    def _extract_outcomes(self, text: str) -> list[str]:
        """Extract outcomes (results, achievements)."""
        # For now, don't extract outcomes deterministically
        # This should be confirmed by user to avoid fabrication
        return []

    def _extract_scope(self, text: str) -> dict[str, str]:
        """Extract scope information (numbers, ranges, etc.)."""
        # Don't extract scope deterministically to avoid guessing numbers
        return {}

    def _identify_unknowns(self, facts: dict[str, Any], text: str) -> list[str]:
        """Identify unknown items that would improve the expression."""
        unknowns = []

        # If actions include literature retrieval, ask about databases
        if "retrieve_literature" in facts["actions"]:
            unknowns.append("databases_used")

        # If methods include meta_analysis, ask about the workflow rather than
        # requiring a remembered study count.
        if "meta_analysis" in facts["methods"]:
            unknowns.append("screening_criteria")

        # If no outcomes are specified, ask about results
        if not facts["outcomes"]:
            unknowns.append("publication_status")
            unknowns.append("project_outcomes")

        # If responsibility is unclear, ask for clarification
        if facts["role"]["responsibility_level"] == "participated":
            unknowns.append("specific_responsibilities")

        return unknowns[:5]  # Limit to 5 unknowns

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

    def _generate_clarifying_questions(self, facts: dict[str, Any], unknowns: list[str]) -> list[str]:
        """Generate clarifying questions to improve the expression."""
        questions = []

        # Prioritize questions that would most impact resume expression
        if "databases_used" in unknowns:
            questions.append("使用了哪些数据库进行文献检索？")

        if "screening_criteria" in unknowns:
            questions.append("你负责了文献筛选、数据提取或质量评价中的哪些环节？")

        if "specific_responsibilities" in unknowns:
            questions.append("你在项目中具体负责哪些任务？")

        if "publication_status" in unknowns:
            questions.append("这个项目是否有发表计划或已发表？")

        return questions[:3]  # Limit to 3 questions as required

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
