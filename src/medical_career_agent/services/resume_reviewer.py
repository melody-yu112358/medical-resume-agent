from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from .resume_intake import ResumeIntakeResult


UPGRADE_TERMS = ("主导", "独立负责", "精通", "核心负责人")


@dataclass(frozen=True)
class ResumeReviewFinding:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ResumeReviewResult:
    findings: tuple[ResumeReviewFinding, ...]
    unproven_requirement_ids: tuple[str, ...]
    quality_checks: tuple[str, ...]
    version: str = "resume-review-v0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResumeReviewService:
    """Deterministic pre-export guard; it flags risk and never rewrites a CV."""

    def review(
        self,
        *,
        intake: ResumeIntakeResult,
        final_resume_text: str,
        confirmed_facts: tuple[str, ...] = (),
    ) -> ResumeReviewResult:
        if not final_resume_text.strip():
            raise ValueError("final_resume_text cannot be empty")
        facts = tuple(item.strip() for item in confirmed_facts if item.strip())
        allowed_text = "\n".join(
            [
                *(item.resume_quote for item in intake.evidence_matches if item.resume_quote),
                *facts,
            ]
        )
        findings: list[ResumeReviewFinding] = []
        allowed_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", allowed_text))
        document_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", final_resume_text))
        added_numbers = sorted(document_numbers - allowed_numbers)
        if added_numbers:
            findings.append(
                ResumeReviewFinding(
                    code="unconfirmed_number",
                    severity="warning",
                    message=f"最终简历出现未在已确认事实中找到的数字：{', '.join(added_numbers)}。请核实或删除。",
                )
            )
        for term in UPGRADE_TERMS:
            if term in final_resume_text and term not in allowed_text:
                findings.append(
                    ResumeReviewFinding(
                        code="responsibility_upgrade",
                        severity="warning",
                        message=f"“{term}”可能扩大了原始职责范围；请确认原始经历可直接支持该表述。",
                    )
                )
        unproven = tuple(
            item.requirement_id
            for item in intake.evidence_matches
            if item.strength == "none"
        )
        if unproven:
            findings.append(
                ResumeReviewFinding(
                    code="unproven_jd_requirement",
                    severity="info",
                    message="部分 JD 要求仍没有可确认的个人证据，不应为了关键词覆盖而补造。",
                )
            )
        if not findings:
            findings.append(
                ResumeReviewFinding(
                    code="no_automatic_risk_found",
                    severity="info",
                    message="未发现数字或职责范围的自动风险提示；仍请本人核对全部事实。",
                )
            )
        return ResumeReviewResult(
            findings=tuple(findings),
            unproven_requirement_ids=unproven,
            quality_checks=(
                "numbers_checked_against_confirmed_sources",
                "responsibility_upgrade_terms_checked",
                "unproven_jd_requirements_retained",
            ),
        )
