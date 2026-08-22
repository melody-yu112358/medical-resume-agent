from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


SECTION_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("education", ("教育背景", "教育经历", "学习经历", "Education", "Education Background")),
    ("clinical_experience", ("临床经历", "临床实习", "临床实践", "轮转经历", "规培经历", "Clinical Experience", "Clinical Rotations")),
    ("professional_experience", ("工作经历", "实习经历", "社会实践", "实践经历", "Work Experience", "Professional Experience", "Internship Experience")),
    (
        "research_experience",
        (
            "科研经历", "研究经历", "科研训练", "学术经历", "科研 / 实践经历",
            "科研 / 学术经历", "研究方向与科研经历", "校园 / 科研经历",
            "Research Experience", "Research Interests",
        ),
    ),
    ("projects", ("项目经历", "项目经验", "Projects", "Project Experience")),
    ("publications", ("论文", "学术成果", "论文 / 学术成果", "发表成果", "会议汇报", "Publications", "Selected Publications", "Presentations")),
    ("awards", ("获奖经历", "荣誉奖项", "荣誉", "奖项", "Awards", "Honors", "Awards and Honors")),
    ("skills", ("技能证书", "技能与证书", "专业技能", "证书", "技能", "Skills", "Technical Skills", "Certifications")),
    ("languages", ("语言能力", "英语能力", "外语能力", "Languages", "Language Skills")),
)


@dataclass(frozen=True)
class ExtractedEvidence:
    evidence_id: str
    statement: str
    source_locator: str
    status: str = "extracted"


@dataclass(frozen=True)
class ResumeSectionCandidate:
    section_key: str
    heading: str
    evidence_ids: tuple[str, ...]
    lines: tuple[str, ...]


@dataclass(frozen=True)
class ResumeStructureResult:
    sections: tuple[ResumeSectionCandidate, ...]
    evidence: tuple[ExtractedEvidence, ...]
    unclassified_lines: tuple[str, ...]
    confirmation_questions: tuple[str, ...]
    version: str = "resume-structure-v0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResumeStructurer:
    """Groups a medical resume by explicit headings without guessing facts.

    This is intentionally a pre-confirmation step. The output does not claim to
    be a valid resume-document-v1 record: imported lines remain `extracted`
    evidence until the user assigns them to a structured item and confirms it.
    """

    def structure(self, *, resume_text: str) -> ResumeStructureResult:
        if not resume_text.strip():
            raise ValueError("resume_text cannot be empty")

        sections: list[ResumeSectionCandidate] = []
        evidence: list[ExtractedEvidence] = []
        unclassified: list[str] = []
        current_key: str | None = None
        current_heading = ""
        current_lines: list[str] = []
        current_ids: list[str] = []

        def close_current() -> None:
            if current_key is not None:
                sections.append(
                    ResumeSectionCandidate(
                        section_key=current_key,
                        heading=current_heading,
                        evidence_ids=tuple(current_ids),
                        lines=tuple(current_lines),
                    )
                )

        for line_number, raw_line in enumerate(resume_text.splitlines(), 1):
            line = self._clean_line(raw_line)
            if not line:
                continue
            matched = self._section_for_heading(line)
            if matched:
                close_current()
                current_key, _ = matched
                current_heading = line
                current_lines, current_ids = [], []
                continue

            evidence_id = f"import-line-{line_number:03d}"
            evidence.append(
                ExtractedEvidence(
                    evidence_id=evidence_id,
                    statement=line,
                    source_locator=f"line {line_number}",
                )
            )
            if current_key is None:
                unclassified.append(line)
            else:
                current_lines.append(line)
                current_ids.append(evidence_id)
        close_current()

        return ResumeStructureResult(
            sections=tuple(sections),
            evidence=tuple(evidence),
            unclassified_lines=tuple(unclassified),
            confirmation_questions=self._questions(sections, unclassified),
        )

    @staticmethod
    def _clean_line(raw_line: str) -> str:
        return re.sub(r"^[\s#>*•●▪◦\-–—]+", "", raw_line).strip()

    @staticmethod
    def _section_for_heading(line: str) -> tuple[str, str] | None:
        normalized = re.sub(r"^[\d一二三四五六七八九十]+[.、）)]*\s*", "", line)
        normalized = normalized.strip("【】[]：: ")
        for key, aliases in SECTION_ALIASES:
            if normalized.casefold() in {alias.casefold() for alias in aliases}:
                return key, normalized
        return None

    @staticmethod
    def _questions(
        sections: list[ResumeSectionCandidate], unclassified: list[str]
    ) -> tuple[str, ...]:
        keys = {section.section_key for section in sections}
        questions = []
        if "education" not in keys:
            questions.append("未识别到教育背景标题；请确认学校、学位、专业和起止时间。")
        if "clinical_experience" not in keys and "professional_experience" not in keys:
            questions.append("未识别到临床、实习或工作经历标题；请确认是否需要补充。")
        if unclassified:
            questions.append("有未归类的原始内容；请将其分配到对应栏目，或确认不在投递稿中展示。")
        return tuple(questions)
