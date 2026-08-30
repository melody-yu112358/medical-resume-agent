"""Bounded model operations for intake summaries and claim rewrites."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from ..ports.repositories import ModelGateway


@dataclass(frozen=True)
class ConversationLanguageResult:
    rewrite_candidate: dict[str, Any] | None = None


@dataclass(frozen=True)
class IntakeSummaryResult:
    """Untrusted Skill-stage summary candidate; the backend validates every ref."""

    candidate: dict[str, Any] | None = None


class ConversationModelGateway(Protocol):
    def summarize_intake_turn(
        self, *, text: str, selected_option_ids: list[str], free_text: str,
        session_context: dict[str, Any], allowed_question_card: dict[str, Any] | None,
    ) -> IntakeSummaryResult:
        """Summarize candidate facts and phrase only the backend-selected gap."""

    def rewrite_claim(self, *, source_claim: dict[str, Any], canonical_experience: dict[str, Any], tone: str, instruction: str) -> ConversationLanguageResult:
        """Return a candidate wording and its complete traceability fields only."""


class ModelGatewayConversationGateway:
    """Adapter over the existing generic ModelGateway with strict JSON filtering."""

    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    @staticmethod
    def _parse_json_object(raw: object) -> dict[str, Any] | None:
        if not isinstance(raw, str):
            return None
        candidate = raw.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1)
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None

    def summarize_intake_turn(
        self, *, text: str, selected_option_ids: list[str], free_text: str,
        session_context: dict[str, Any], allowed_question_card: dict[str, Any] | None,
    ) -> IntakeSummaryResult:
        allowed_card = allowed_question_card or {}
        raw = self.gateway.generate(task="resume_intake_skill_summary", context={
            "instruction": "Return JSON only. Work under Medical Resume Skill Stage 1. Select only the backend fact refs that best summarize the user's evidence; do not write summary prose. The backend renders all candidate-facing wording. Preserve participation and responsibility boundaries, never create or confirm a fact, number, outcome, tool, method, or ownership level. allowed_fact_refs is the complete fact whitelist. evidence_quotes must be non-empty verbatim substrings from one active_evidence record. For the next gap, copy the supplied question_id exactly and recommend only its option IDs; do not write or rewrite question text. Do not decide readiness, canonical data, confirmation, claims, or audit status.",
            "user_answer": {
                "display_text": text, "selected_option_ids": selected_option_ids,
                "free_text": free_text,
            },
            "active_evidence": session_context.get("active_evidence", []),
            "extracted_facts": session_context.get("extracted_facts", {}),
            "allowed_fact_refs": session_context.get("allowed_fact_refs", []),
            "confirmed_facts": session_context.get("confirmed_facts"),
            "previous_questions": session_context.get("previous_questions", []),
            "allowed_question_card": allowed_card,
            "response_shape": {
                "summary": {"fact_refs": ["actions:screen_studies"], "evidence_quotes": ["verbatim user substring"]},
                "next_question": {"question_id": allowed_card.get("question_id"), "recommended_option_ids": []},
            },
        })
        value = self._parse_json_object(raw)
        return IntakeSummaryResult(candidate=value if isinstance(value, dict) else None)

    def rewrite_claim(self, *, source_claim: dict[str, Any], canonical_experience: dict[str, Any], tone: str, instruction: str) -> ConversationLanguageResult:
        raw = self.gateway.generate(task="resume_constrained_rewrite", context={
            "instruction": "Return JSON only. Rewrite wording using only source_claim used_facts, dependency_refs and evidence_ids. Never add facts, activities, responsibility, numbers or outcomes. Conservative is concise and literal, foregrounding guidance/partial limits; Professional is denser and orders action, method/tool and scope; High-impact uses more active ordering and professional-value emphasis for the same confirmed contribution only. Never use 主导, 项目负责人, 负责全部, 完整流程, 熟练掌握, or stronger equivalents without explicit source support. Copy used_facts, dependency_refs and evidence_ids verbatim unchanged. Return wording, used_facts, dependency_refs and evidence_ids.",
            "tone": tone, "user_instruction": instruction,
            "source_claim": source_claim, "canonical_experience": canonical_experience,
        })
        value = self._parse_json_object(raw)
        if value is None:
            return ConversationLanguageResult()
        return ConversationLanguageResult(rewrite_candidate=value if isinstance(value, dict) else None)
