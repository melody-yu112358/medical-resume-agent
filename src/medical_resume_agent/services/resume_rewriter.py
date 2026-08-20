from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from ..ports import ModelGateway
from .resume_intake import ResumeIntakeResult


class ResumeRewriteRejectedError(RuntimeError):
    pass


REWRITE_TASK = """
你是医学生求职简历的受约束改写层。只使用输入 JSON 中的 resume_quote 和
confirmed_facts，不得新增经历、技能、数字、结果、职级或职责范围。只改写已有证据，
没有证据的 JD 要求必须跳过。输出严格 JSON，不要 Markdown：
{"items":[{"requirement_id":"req-01","source_quote":"原文逐字复制",
"rewritten":"改写后的单条简历表述","reason":"为何更对应JD"}]}
source_quote 必须逐字复制输入证据或 confirmed_facts。不要输出其他字段。
""".strip()

UPGRADE_TERMS = ("主导", "独立负责", "精通", "显著提升", "大幅提升", "核心负责人")


@dataclass(frozen=True)
class ResumeRewriteItem:
    requirement_id: str
    requirement: str
    source_quote: str
    rewritten: str
    reason: str


@dataclass(frozen=True)
class ResumeRewriteResult:
    items: tuple[ResumeRewriteItem, ...]
    skipped_requirement_ids: tuple[str, ...]
    quality_checks: tuple[str, ...]
    mode: str = "model_grounded_rewrite"
    notice: str | None = None
    version: str = "resume-rewrite-gate-v0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResumeRewriteService:
    def __init__(self, model: ModelGateway) -> None:
        self.model = model

    def rewrite(
        self,
        *,
        intake: ResumeIntakeResult,
        confirmed_facts: tuple[str, ...] = (),
    ) -> ResumeRewriteResult:
        facts = tuple(item.strip() for item in confirmed_facts if item.strip())
        evidence = [
            {
                "requirement_id": item.requirement_id,
                "requirement": item.requirement,
                "resume_quote": item.resume_quote,
                "strength": item.strength,
            }
            for item in intake.evidence_matches
            if item.resume_quote
        ]
        context = {"evidence": evidence, "confirmed_facts": facts}
        raw = self.model.generate(task=REWRITE_TASK, context=context)
        payload = self._parse(raw)
        items = self._validate(payload, intake, facts)
        rewritten_ids = {item.requirement_id for item in items}
        skipped = tuple(
            item.requirement_id
            for item in intake.evidence_matches
            if item.requirement_id not in rewritten_ids
        )
        return ResumeRewriteResult(
            items=items,
            skipped_requirement_ids=skipped,
            quality_checks=(
                "source_quote_is_verbatim",
                "numbers_are_grounded",
                "responsibility_is_not_upgraded",
                "requirement_id_is_valid",
            ),
        )

    @staticmethod
    def _parse(raw: str) -> dict[str, object]:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ResumeRewriteRejectedError("model output is not valid JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise ResumeRewriteRejectedError("model output must contain an items array")
        return payload

    @staticmethod
    def _validate(
        payload: dict[str, object],
        intake: ResumeIntakeResult,
        facts: tuple[str, ...],
    ) -> tuple[ResumeRewriteItem, ...]:
        matches = {item.requirement_id: item for item in intake.evidence_matches}
        allowed_sources = {item.resume_quote for item in matches.values() if item.resume_quote}
        allowed_sources.update(facts)
        result = []
        seen = set()
        for raw_item in payload["items"]:
            if not isinstance(raw_item, dict):
                raise ResumeRewriteRejectedError("each rewrite item must be an object")
            requirement_id = str(raw_item.get("requirement_id", ""))
            source = str(raw_item.get("source_quote", "")).strip()
            rewritten = str(raw_item.get("rewritten", "")).strip()
            reason = str(raw_item.get("reason", "")).strip()
            if requirement_id not in matches or requirement_id in seen:
                raise ResumeRewriteRejectedError("rewrite used an invalid requirement_id")
            if source not in allowed_sources:
                raise ResumeRewriteRejectedError("source_quote is not a confirmed verbatim fact")
            if not rewritten or not reason:
                raise ResumeRewriteRejectedError("rewrite and reason cannot be empty")
            source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", source))
            output_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", rewritten))
            if output_numbers - source_numbers:
                raise ResumeRewriteRejectedError("rewrite added an unconfirmed number")
            invented_upgrade = next(
                (term for term in UPGRADE_TERMS if term in rewritten and term not in source),
                None,
            )
            if invented_upgrade:
                raise ResumeRewriteRejectedError(
                    f"rewrite upgraded responsibility without evidence: {invented_upgrade}"
                )
            match = matches[requirement_id]
            result.append(
                ResumeRewriteItem(
                    requirement_id=requirement_id,
                    requirement=match.requirement,
                    source_quote=source,
                    rewritten=rewritten,
                    reason=reason,
                )
            )
            seen.add(requirement_id)
        if not result:
            raise ResumeRewriteRejectedError("model returned no grounded rewrite items")
        return tuple(result)


def evidence_preserving_rewrite(intake: ResumeIntakeResult) -> ResumeRewriteResult:
    """Keep the demo usable without a model while never manufacturing wording."""
    items = tuple(
        ResumeRewriteItem(
            requirement_id=item.requirement_id,
            requirement=item.requirement,
            source_quote=item.resume_quote,
            rewritten=item.resume_quote,
            reason="当前未配置改写模型，保留可追溯的原始表述；可在最终简历中手动精简和调整顺序。",
        )
        for item in intake.evidence_matches
        if item.resume_quote
    )
    if not items:
        raise ResumeRewriteRejectedError("no grounded evidence is available for a draft")
    rewritten_ids = {item.requirement_id for item in items}
    return ResumeRewriteResult(
        items=items,
        skipped_requirement_ids=tuple(
            item.requirement_id
            for item in intake.evidence_matches
            if item.requirement_id not in rewritten_ids
        ),
        quality_checks=(
            "source_quote_is_verbatim",
            "model_was_not_used",
            "unproven_requirements_were_skipped",
        ),
        mode="evidence_preserving_fallback",
        notice="当前未配置模型：已生成只保留原始证据的候选条目，不包含 AI 改写。",
    )
