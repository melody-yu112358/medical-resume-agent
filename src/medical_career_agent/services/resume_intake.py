from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


HARD_MARKERS = ("必须", "要求", "本科", "硕士", "博士", "专业", "经验", "年", "资格")
BONUS_MARKERS = ("优先", "加分", "熟悉", "有经验者", "preferred")
RESPONSIBILITY_MARKERS = ("负责", "参与", "支持", "协助", "开展", "完成", "推动")
SKILL_TERMS = (
    "医学", "临床", "文献", "写作", "数据", "统计", "沟通", "协作", "项目",
    "英语", "gcp", "sop", "合规", "产品", "需求", "python", "r语言", "excel",
)
ACTION_TERMS = ("负责", "完成", "开展", "撰写", "分析", "协调", "汇报", "推动", "设计")


@dataclass(frozen=True)
class JdRequirement:
    requirement_id: str
    text: str
    category: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceMatch:
    requirement_id: str
    requirement: str
    resume_quote: str | None
    matched_keywords: tuple[str, ...]
    strength: str
    gap_type: str | None
    reason: str


@dataclass(frozen=True)
class ResumeIntakeResult:
    requirements: tuple[JdRequirement, ...]
    evidence_matches: tuple[EvidenceMatch, ...]
    questions: tuple[str, ...]
    version: str = "resume-intake-v0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResumeIntakeService:
    """Deterministic JD analysis and evidence selection before any LLM rewrite."""

    def analyze(self, *, resume_text: str, jd_text: str) -> ResumeIntakeResult:
        if not resume_text.strip():
            raise ValueError("resume_text cannot be empty")
        if not jd_text.strip():
            raise ValueError("jd_text cannot be empty")

        requirements = self._requirements(jd_text)
        sentences = self._sentences(resume_text)
        matches = tuple(self._match(item, sentences) for item in requirements)
        questions = self._questions(matches)
        return ResumeIntakeResult(requirements, matches, questions)

    def _requirements(self, text: str) -> tuple[JdRequirement, ...]:
        lines = self._sentences(text)[:16]
        result = []
        for index, line in enumerate(lines, 1):
            lower = line.lower()
            if any(marker in lower for marker in BONUS_MARKERS):
                category = "bonus"
            elif any(marker in lower for marker in HARD_MARKERS):
                category = "hard_requirement"
            elif any(marker in lower for marker in RESPONSIBILITY_MARKERS):
                category = "responsibility"
            else:
                category = "skill_keyword"
            keywords = tuple(term for term in SKILL_TERMS if term in lower)
            result.append(JdRequirement(f"req-{index:02d}", line, category, keywords))
        return tuple(result)

    def _match(self, requirement: JdRequirement, sentences: tuple[str, ...]) -> EvidenceMatch:
        candidates = []
        for sentence in sentences:
            lower = sentence.lower()
            overlap = tuple(term for term in requirement.keywords if term in lower)
            if overlap:
                candidates.append((len(overlap), sentence, overlap))
        if not candidates:
            return EvidenceMatch(
                requirement.requirement_id, requirement.text, None, (), "none",
                "missing_evidence", "简历中没有找到能直接支持该要求的原文。",
            )
        _, quote, overlap = max(candidates, key=lambda item: (item[0], len(item[1])))
        has_action = any(term in quote.lower() for term in ACTION_TERMS)
        has_result = bool(re.search(r"\d|%|篇|项|人|例|次|个月|年", quote))
        if has_action and has_result:
            strength, gap, reason = "strong", None, "同时包含本人行动和可核实结果线索。"
        elif has_action:
            strength, gap, reason = "medium", "needs_quantification", "有行动，但缺少规模、交付物或结果。"
        else:
            strength, gap, reason = "weak", "ambiguous_evidence", "只出现相关关键词，尚不能证明实际做过。"
        return EvidenceMatch(
            requirement.requirement_id, requirement.text, quote, overlap,
            strength, gap, reason,
        )

    def _questions(self, matches: tuple[EvidenceMatch, ...]) -> tuple[str, ...]:
        questions = []
        for item in matches:
            if item.gap_type == "missing_evidence":
                questions.append(
                    f"你是否有真实经历能证明“{item.requirement}”？如果有，请说明情境、本人行动和结果。"
                )
            elif item.gap_type == "needs_quantification":
                questions.append(
                    f"关于“{item.resume_quote}”，可以补充周期、数量、交付物或结果吗？"
                )
            elif item.gap_type == "ambiguous_evidence":
                questions.append(
                    f"简历提到“{item.resume_quote}”，你本人具体做了什么？"
                )
            if len(questions) == 8:
                break
        return tuple(questions)

    @staticmethod
    def _sentences(text: str) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                cleaned
                for fragment in re.split(r"[\n；;。]+|(?=\d+[.、])", text)
                if (cleaned := re.sub(r"^[-•*\s\d.、]+", "", fragment).strip())
            )
        )

