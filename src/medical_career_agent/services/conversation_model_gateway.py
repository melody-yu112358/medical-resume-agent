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
    rewrite_candidates: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class IntakeSummaryResult:
    """Untrusted Skill-stage summary candidate; the backend validates every ref."""

    candidate: dict[str, Any] | None = None


class ConversationModelGateway(Protocol):
    def summarize_intake_turn(
        self, *, text: str, selected_option_ids: list[str], free_text: str,
        session_context: dict[str, Any], allowed_question_cards: list[dict[str, Any]],
    ) -> IntakeSummaryResult:
        """Summarize facts and select one backend-owned unresolved gap."""

    def rewrite_claim(self, *, source_claim: dict[str, Any], canonical_experience: dict[str, Any], tone: str, instruction: str) -> ConversationLanguageResult:
        """Return a candidate wording and its complete traceability fields only."""

    def rewrite_experience_tiers(
        self, *, source_claims: list[dict[str, Any]],
        canonical_experience: dict[str, Any], instruction: str,
    ) -> ConversationLanguageResult:
        """Return all three expression tiers for one experience in one call."""


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
        session_context: dict[str, Any], allowed_question_cards: list[dict[str, Any]],
    ) -> IntakeSummaryResult:
        allowed_cards = allowed_question_cards or []
        example_card = allowed_cards[0] if allowed_cards else {}
        raw = self.gateway.generate(task="resume_intake_skill_summary", context={
            "instruction": "Return JSON only. Work under Medical Resume Skill Stage 1. Select only the backend fact refs that best summarize the user's evidence; do not write summary prose. The backend renders all candidate-facing wording. Preserve participation and responsibility boundaries, never create or confirm a fact, number, outcome, tool, method, or ownership level. allowed_fact_refs is the complete fact whitelist. evidence_quotes must be non-empty verbatim substrings from one active_evidence record. Select the single highest-value unresolved gap from allowed_question_cards by copying its question_id exactly, then recommend only option IDs from that same card. Do not write or rewrite question text. Do not decide readiness, canonical data, confirmation, claims, or audit status.",
            "user_answer": {
                "display_text": text, "selected_option_ids": selected_option_ids,
                "free_text": free_text,
            },
            "active_evidence": session_context.get("active_evidence", []),
            "extracted_facts": session_context.get("extracted_facts", {}),
            "allowed_fact_refs": session_context.get("allowed_fact_refs", []),
            "confirmed_facts": session_context.get("confirmed_facts"),
            "previous_questions": session_context.get("previous_questions", []),
            "allowed_question_cards": allowed_cards,
            "response_shape": {
                "summary": {"fact_refs": ["actions:screen_studies"], "evidence_quotes": ["verbatim user substring"]},
                "next_question": {"question_id": example_card.get("question_id"), "recommended_option_ids": []},
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

    def rewrite_experience_tiers(
        self, *, source_claims: list[dict[str, Any]],
        canonical_experience: dict[str, Any], instruction: str,
    ) -> ConversationLanguageResult:
        raw = self.gateway.generate(task="resume_experience_tier_rewrite", context={
            "instruction": "Return JSON only. For every source claim, return exactly one Conservative, one Professional, and one High-impact candidate. Rewrite wording only; copy source_claim_id, used_facts, dependency_refs and evidence_ids verbatim. Never add facts, activities, responsibility, numbers or outcomes. The three wordings must be substantively distinct, not punctuation or synonym swaps. Conservative states the narrowest confirmed contribution and any real limit. Professional combines action, method/tool, scope and deliverable when those fields exist. High-impact front-loads the strongest confirmed contribution and explains its target-role value or technical complexity without adding a result or upgrading ownership. Responsibility words are immutable per source claim: preserve that source wording's 参与, 协助, 负责, 独立, 主导, and 在指导下 meaning in all three candidates; never add, remove, strengthen, or move one of those meanings to another source claim. Never use 主导, 项目负责人, 负责全部, 完整流程, 独立完成, 熟练掌握, or stronger equivalents unless that exact responsibility or scope is explicitly supported by the same source claim and canonical responsibility. Do not add '在指导下' merely because a supervisor exists; use it only when the source activity execution_mode is supervised. Return a flat rewrite_candidates array. Do not omit a source/tone pair.",
            "user_instruction": instruction,
            "source_claims": source_claims,
            "canonical_experience": canonical_experience,
            "response_shape": {
                "rewrite_candidates": [{
                    "source_claim_id": "claim_id", "tone": "Conservative|Professional|High-impact",
                    "wording": "candidate wording", "used_facts": [],
                    "dependency_refs": {}, "evidence_ids": [],
                }],
            },
        })
        value = self._parse_json_object(raw)
        candidates = (value or {}).get("rewrite_candidates")
        if not isinstance(candidates, list):
            return ConversationLanguageResult()
        return ConversationLanguageResult(
            rewrite_candidates=[item for item in candidates if isinstance(item, dict)],
        )
