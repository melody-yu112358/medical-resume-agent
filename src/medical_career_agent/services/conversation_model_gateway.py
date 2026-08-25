"""Language-only boundary for the resume conversation.

The gateway may interpret intent and improve question wording, but it returns a
small candidate command only.  The conversation orchestrator remains solely
responsible for changing persisted state and always sends factual changes to
the deterministic confirmation and claim-gate services.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from ..ports.repositories import ModelGateway


@dataclass(frozen=True)
class ConversationLanguageResult:
    intent: str | None = None
    assistant_message: str | None = None
    activity_proposals: list[dict[str, Any]] | None = None
    rewrite_candidate: dict[str, Any] | None = None


class ConversationModelGateway(Protocol):
    def interpret(self, *, text: str, stage: str, pending_questions: list[str]) -> ConversationLanguageResult:
        """Return a bounded candidate intent; never return facts or state patches."""

    def propose_activities(self, *, text: str, extracted_facts: dict[str, Any]) -> ConversationLanguageResult:
        """Return candidate activities only; the orchestrator validates and persists proposals."""

    def rewrite_claim(self, *, source_claim: dict[str, Any], canonical_experience: dict[str, Any], tone: str, instruction: str) -> ConversationLanguageResult:
        """Return a candidate wording and its complete traceability fields only."""


class ModelGatewayConversationGateway:
    """Adapter over the existing generic ModelGateway with strict JSON filtering."""

    _ALLOWED_INTENTS = {"confirm_facts", "update_facts", "select_role_packs", "edit_wording", "accept_bullets"}

    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    def interpret(self, *, text: str, stage: str, pending_questions: list[str]) -> ConversationLanguageResult:
        raw = self.gateway.generate(task="resume_conversation_intent", context={
            "instruction": "Classify only. Return JSON with intent (or null) and assistant_message (or null). Do not extract facts, invent facts, or return state changes.",
            "allowed_intents": sorted(self._ALLOWED_INTENTS),
            "stage": stage, "pending_questions": pending_questions[:3], "user_text": text,
        })
        try:
            value = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return ConversationLanguageResult()
        if not isinstance(value, dict):
            return ConversationLanguageResult()
        intent = value.get("intent")
        message = value.get("assistant_message")
        return ConversationLanguageResult(
            intent=intent if intent in self._ALLOWED_INTENTS else None,
            assistant_message=message.strip() if isinstance(message, str) and len(message.strip()) <= 500 else None,
        )

    def propose_activities(self, *, text: str, extracted_facts: dict[str, Any]) -> ConversationLanguageResult:
        raw = self.gateway.generate(task="resume_activity_proposals", context={
            "instruction": "Return JSON only. Propose atomic activities, never facts outside vocabulary. Each proposal needs evidence_quote copied verbatim from user_text, components, ownership_level, execution_mode, and coverage. Split different actions or responsibility boundaries into separate activities. Use unknown for any ownership, execution, or coverage dimension not explicitly supported by the quote; never infer supervised from a mentor defining a plan, or partial from collaboration alone. Do not return canonical data or state patches.",
            "user_text": text,
            "allowed_components": {key: extracted_facts.get(key, []) for key in ("actions", "methods", "tools", "techniques", "objects", "artifacts")},
            "ownership_levels": ["unknown", "contributed", "owned_component", "led_delivery", "accountable"],
            "execution_modes": ["unknown", "supervised", "independent", "shared"],
            "coverage": ["unknown", "full", "partial"],
            "response_shape": {"activity_proposals": [{"evidence_quote": "verbatim substring", "components": {"actions": [], "methods": [], "tools": [], "techniques": [], "objects": [], "artifacts": []}, "ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown", "scope_note": None}]},
        })
        try:
            value = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return ConversationLanguageResult(activity_proposals=[])
        proposals = value.get("activity_proposals") if isinstance(value, dict) else None
        return ConversationLanguageResult(activity_proposals=proposals if isinstance(proposals, list) else [])

    def rewrite_claim(self, *, source_claim: dict[str, Any], canonical_experience: dict[str, Any], tone: str, instruction: str) -> ConversationLanguageResult:
        raw = self.gateway.generate(task="resume_constrained_rewrite", context={
            "instruction": "Return JSON only. Rewrite only source_claim wording. Copy source_claim used_facts, dependency_refs and evidence_ids verbatim and unchanged. Never switch activity, responsibility, facts, evidence, numbers, outcomes, ownership, execution, or scope. Conservative is plainer; Professional is more polished; High-impact may improve ordering and action verbs but cannot strengthen responsibility. Return wording, used_facts, dependency_refs and evidence_ids.",
            "tone": tone, "user_instruction": instruction,
            "source_claim": source_claim, "canonical_experience": canonical_experience,
        })
        try:
            value = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return ConversationLanguageResult()
        return ConversationLanguageResult(rewrite_candidate=value if isinstance(value, dict) else None)
