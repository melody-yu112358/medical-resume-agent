"""State-aware orchestration for the conversational resume workspace.

This layer deliberately contains no free-form model generation.  It routes user
messages through the existing extraction, confirmation, composition and claim
audit services, and persists the resulting source-of-truth state in sessions.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from ..adapters.file_session_store import FileSessionStore
from .bullet_composer import BulletComposerService
from .claim_gate import ClaimGateService
from .claim_ledger import ClaimLedgerService
from .confirmation_gate import ConfirmationGateService
from .experience_draft import ExperienceDraftService
from .conversation_model_gateway import ConversationModelGateway


STAGES = (
    "intake", "fact_confirmation", "representative_sample", "composition",
    "factual_audit", "delivery",
)


class ResumeConversationAgent:
    """Bounded conversation coordinator; canonical facts remain the authority."""

    def __init__(
        self, *, sessions: FileSessionStore, experience_drafter: ExperienceDraftService,
        confirmation_gate: ConfirmationGateService, bullet_composer: BulletComposerService,
        claim_gate: ClaimGateService, claim_ledger: ClaimLedgerService,
        language_gateway: ConversationModelGateway | None = None,
    ) -> None:
        self.sessions = sessions
        self.experience_drafter = experience_drafter
        self.confirmation_gate = confirmation_gate
        self.bullet_composer = bullet_composer
        self.claim_gate = claim_gate
        self.claim_ledger = claim_ledger
        self.language_gateway = language_gateway

    @staticmethod
    def initial_state() -> dict[str, Any]:
        return {
            "conversation_version": "resume-conversation-v1", "stage": "intake",
            "raw_user_texts": [], "extracted_draft": None,
            "confirmed_canonical_experience": None, "evidence_records": [],
            "pending_questions": [], "selected_role_packs": [], "generated_claims": [],
            "claim_gate_results": {}, "claim_user_dispositions": {},
            "activity_proposals": [], "rewrite_candidates": [], "resume_document": None,
            "proposal_audits": [], "language_audit": [],
        }

    def create(self, session_id: str | None = None) -> dict[str, Any]:
        created = self.sessions.create(session_id)
        self.sessions.update(created, state=self.initial_state())
        return self.read(created)

    def read(self, session_id: str) -> dict[str, Any]:
        payload = self.sessions.get(session_id)
        state = self.initial_state()
        stored = payload.get("state", {})
        if isinstance(stored, dict):
            state.update(stored)
        state["resume_document"] = self._resume_document(session_id, state)
        return {"session_id": session_id, "state": state, "events": payload.get("events", [])}

    def handle_message(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self.read(session_id)
        state = session["state"]
        text = str(payload.get("text", "")).strip()
        action = str(payload.get("action", "")).strip()
        language_message = None
        if not action and text and self.language_gateway is not None and state["stage"] != "intake":
            # The model may suggest a whitelisted intent and a friendlier question;
            # it cannot provide facts, mutations, or audit decisions.
            language = self.language_gateway.interpret(
                text=text, stage=state["stage"], pending_questions=state["pending_questions"],
            )
            allowed_intents = self._allowed_language_intents(state["stage"])
            action = language.intent if language.intent in allowed_intents else action
            language_message = language.assistant_message
            state["language_audit"].append({
                "stage": state["stage"], "model_intent": language.intent,
                "applied_intent": action or None,
            })
        if text:
            state["raw_user_texts"].append(text)

        if action == "confirm_facts":
            response = self._confirm(session_id, state, payload)
        elif action == "confirm_activity_proposals":
            response = self._confirm_activity_proposals(session_id, state, payload)
        elif action == "reject_activity_proposal":
            response = self._reject_activity_proposal(state, payload)
        elif action == "update_activity_proposals":
            response = self._update_activity_proposals(state, payload)
        elif action == "split_activity_proposal":
            response = self._split_activity_proposal(state, payload)
        elif action == "merge_activity_proposals":
            response = self._merge_activity_proposals(state, payload)
        elif action == "update_facts":
            state["stage"] = "fact_confirmation"
            response = self._supplement_facts(state, payload, text)
        elif action == "select_role_packs":
            response = self._compose(session_id, state, payload)
        elif action == "edit_wording":
            response = self._edit_wording(session_id, state, payload)
        elif action == "rewrite_claim":
            response = self._rewrite_claim(session_id, state, payload)
        elif action == "select_rewrite_candidate":
            response = self._select_rewrite_candidate(state, payload)
        elif action == "accept_bullets":
            state["stage"] = "delivery"
            response = self._response(state, "已保存可交付的已审计要点。", ui_events=["delivery_ready"])
        elif state["stage"] == "intake":
            response = self._intake(state, payload, text)
        elif state["stage"] == "fact_confirmation":
            # Any free-text addition is treated as a proposed fact change, never as a
            # silent edit to canonical facts.  It must be confirmed in a later turn.
            response = self._supplement_facts(state, payload, text)
        else:
            response = self._response(state, "请选择目标方向、确认事实，或提交需要审计的候选措辞。")

        state["resume_document"] = self._resume_document(session_id, state)
        self.sessions.update(session_id, state=state)
        self.sessions.append_event(session_id, {"type": "conversation_message", "action": action or "message", "stage": state["stage"]})
        response["resume_document"] = state["resume_document"]
        if language_message and response["assistant_message"]:
            response["assistant_message"] = f"{language_message}\n\n{response['assistant_message']}"
        response["stage"] = state["stage"]
        response["audit_status"] = self._audit_status(state)
        return response

    def _intake(self, state: dict[str, Any], payload: dict[str, Any], text: str) -> dict[str, Any]:
        if not text:
            return self._response(state, "请用自然语言描述一段真实经历；我会先提取事实，再请你确认。")
        if payload.get("consent_confirmed") is not True:
            return self._response(state, "请先确认这段经历真实准确并同意在本机服务处理后再继续。")
        draft = self.experience_drafter.draft(experience_text=text, context_hint=payload.get("context_hint"), consent_confirmed=True).to_dict()
        state["extracted_draft"] = draft
        state["evidence_records"] = [{"evidence_id": "ev_001", "source_text": text, "status": "confirmed"}]
        state["pending_questions"] = draft["clarifying_questions"]
        state["stage"] = "fact_confirmation"
        self._propose_activities(state, text, draft["extracted_facts"])
        return self._response(state, "我已提取出候选事实和待确认的活动卡。请确认、修改、拆分或拒绝；未确认内容不会进入简历。", pending_question=draft["clarifying_questions"][0] if draft["clarifying_questions"] else None, ui_events=["show_fact_card", "show_activity_cards"])

    def _supplement_facts(self, state: dict[str, Any], payload: dict[str, Any], text: str) -> dict[str, Any]:
        if not text:
            return self._response(state, "请确认事实卡，或补充一条可核实的事实。", pending_question=(state["pending_questions"] or [None])[0])
        draft = self.experience_drafter.draft(experience_text=text, context_hint=payload.get("context_hint"), consent_confirmed=True).to_dict()
        previous = state.get("extracted_draft") or {"extracted_facts": {}}
        merged = deepcopy(previous)
        merged["extracted_facts"] = self._merge_facts(previous.get("extracted_facts", {}), draft["extracted_facts"])
        merged["clarifying_questions"] = draft["clarifying_questions"]
        merged["unknown_items"] = list(dict.fromkeys((previous.get("unknown_items", []) + draft["unknown_items"])))
        state["extracted_draft"] = merged
        next_id = f"ev_{len(state['evidence_records']) + 1:03d}"
        state["evidence_records"].append({"evidence_id": next_id, "source_text": text, "status": "confirmed"})
        state["pending_questions"] = merged["clarifying_questions"]
        self._propose_activities(state, text, merged["extracted_facts"])
        return self._response(state, "已将补充内容作为待确认事实和活动提议加入；确认前不会改变简历或既有 claim。", pending_question=(merged["clarifying_questions"] or [None])[0], ui_events=["refresh_fact_card", "show_activity_cards"])

    def _propose_activities(self, state: dict[str, Any], text: str, facts: dict[str, Any]) -> None:
        if self.language_gateway is not None:
            candidate = self.language_gateway.propose_activities(text=text, extracted_facts=facts).activity_proposals or []
            source = "model"
        else:
            candidate = self._deterministic_activity_proposals(text, facts)
            source = "deterministic_fallback"
        valid, audit = self._validate_activity_proposals_with_audit(candidate, text, facts)
        state["proposal_audits"].append({"source": source, **audit})
        state["activity_proposals"].extend(valid)

    @staticmethod
    def _deterministic_activity_proposals(text: str, facts: dict[str, Any]) -> list[dict[str, Any]]:
        """Fallback proposes facts only; it never invents execution or scope."""
        return [{"evidence_quote": text, "components": {"actions": [action], "methods": facts.get("methods", []), "tools": facts.get("tools", []), "techniques": facts.get("techniques", []), "objects": facts.get("objects", []), "artifacts": facts.get("artifacts", [])}, "ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown", "scope_note": None} for action in facts.get("actions", [])]

    def _validate_activity_proposals(self, proposals: list[dict[str, Any]], source_text: str, facts: dict[str, Any]) -> list[dict[str, Any]]:
        return self._validate_activity_proposals_with_audit(proposals, source_text, facts)[0]

    def _validate_activity_proposals_with_audit(self, proposals: list[dict[str, Any]], source_text: str, facts: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        valid: list[dict[str, Any]] = []
        audit: dict[str, Any] = {"submitted_proposals": [], "hard_rejections": [], "accepted_count": 0}
        categories = ("actions", "methods", "tools", "techniques", "objects", "artifacts")
        for index, raw in enumerate(proposals):
            if not isinstance(raw, dict):
                audit["hard_rejections"].append({"index": index, "reason": "proposal_must_be_object"})
                continue
            audit["submitted_proposals"].append({key: raw.get(key) for key in ("evidence_quote", "components", "ownership_level", "execution_mode", "coverage", "scope_note")})
            quote = raw.get("evidence_quote")
            components = raw.get("components")
            if not isinstance(quote, str) or not quote.strip() or quote not in source_text or not isinstance(components, dict):
                audit["hard_rejections"].append({"index": index, "reason": "evidence_quote_must_be_nonempty_verbatim_source_substring_and_components_object"})
                continue
            # Regex extraction is a semantic signal only, not the final judge:
            # it may miss a valid implicit statement that needs user review.
            quote_facts = self.experience_drafter.draft(experience_text=quote, consent_confirmed=True).extracted_facts
            if any(not isinstance(components.get(category, []), list) for category in categories):
                audit["hard_rejections"].append({"index": index, "reason": "component_categories_must_be_arrays"})
                continue
            normalised = {category: list(components.get(category, [])) for category in categories}
            if not normalised["actions"]:
                audit["hard_rejections"].append({"index": index, "reason": "atomic_activity_requires_action"})
                continue
            if any(set(values) - set(facts.get(category, [])) for category, values in normalised.items()):
                audit["hard_rejections"].append({"index": index, "reason": "component_not_in_extracted_vocabulary"})
                continue
            semantic_warnings = [f"quote does not deterministically expose {category}:{value}" for category, values in normalised.items() for value in values if value not in quote_facts.get(category, [])]
            if raw.get("ownership_level") not in {"unknown", "contributed", "owned_component", "led_delivery", "accountable"} or raw.get("execution_mode") not in {"unknown", "supervised", "independent", "shared"} or raw.get("coverage") not in {"unknown", "full", "partial"}:
                audit["hard_rejections"].append({"index": index, "reason": "invalid_responsibility_enum"})
                continue
            semantic_warnings.extend(self._responsibility_semantic_warnings(quote, raw))
            valid.append({"proposal_id": f"proposal_{uuid4().hex[:8]}", "activity_id": f"act_{uuid4().hex[:8]}", "responsibility_id": f"resp_{uuid4().hex[:8]}", "evidence_quote": quote, "components": normalised, "ownership_level": raw["ownership_level"], "execution_mode": raw["execution_mode"], "scope": {"coverage": raw["coverage"], "note": raw.get("scope_note")}, "semantic_warnings": semantic_warnings, "status": "needs_user_confirmation"})
        audit["accepted_count"] = len(valid)
        return valid, audit

    @staticmethod
    def _responsibility_semantic_warnings(quote: str, proposal: dict[str, Any]) -> list[str]:
        """Flag unsupported boundary inferences without rejecting semantic proposals."""
        warnings: list[str] = []
        explicit = {
            "supervised": ("指导", "带我", "示范"),
            "independent": ("独立", "自己"),
            "shared": ("共同", "团队", "一起", "协作"),
            "partial": ("部分", "一部分", "部分步骤", "其中"),
        }
        execution = proposal.get("execution_mode")
        if execution in explicit and not any(token in quote for token in explicit[execution]):
            warnings.append(f"execution_mode:{execution} is not explicit in evidence quote; user confirmation required")
        coverage = proposal.get("coverage")
        if coverage == "partial" and not any(token in quote for token in explicit["partial"]):
            warnings.append("coverage:partial is not explicit in evidence quote; user confirmation required")
        if proposal.get("ownership_level") in {"led_delivery", "accountable"} and not any(token in quote for token in ("主导", "负责", "牵头", "负责人")):
            warnings.append("strong ownership is not explicit in evidence quote; user confirmation required")
        return warnings

    def _reject_activity_proposal(self, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        proposal_id = str(payload.get("proposal_id", ""))
        for proposal in state["activity_proposals"]:
            if proposal["proposal_id"] == proposal_id:
                proposal["status"] = "rejected"
                return self._response(state, "已拒绝该活动提议；canonical experience 未改变。", ui_events=["refresh_activity_cards"])
        return self._response(state, "未找到该活动提议。")

    def _update_activity_proposals(self, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        source = "\n".join(state["raw_user_texts"])
        facts = (state.get("extracted_draft") or {}).get("extracted_facts", {})
        proposals = self._validate_activity_proposals(payload.get("activity_proposals", []), source, facts)
        if not proposals:
            return self._response(state, "修改后的活动提议未通过原文、事实或范围校验。")
        state["activity_proposals"] = proposals
        return self._response(state, "已更新活动提议；请确认后写入经历。", ui_events=["refresh_activity_cards"])

    def _split_activity_proposal(self, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        proposal = next((item for item in state["activity_proposals"] if item["proposal_id"] == payload.get("proposal_id") and item["status"] == "needs_user_confirmation"), None)
        groups = payload.get("component_groups", [])
        if not proposal or not isinstance(groups, list) or len(groups) < 2:
            return self._response(state, "请提供至少两个待验证的活动拆分。")
        raw = [{"evidence_quote": proposal["evidence_quote"], "components": group, "ownership_level": proposal["ownership_level"], "execution_mode": proposal["execution_mode"], "coverage": proposal["scope"]["coverage"], "scope_note": proposal["scope"].get("note")} for group in groups]
        replacements = self._validate_activity_proposals(raw, "\n".join(state["raw_user_texts"]), (state.get("extracted_draft") or {}).get("extracted_facts", {}))
        if len(replacements) != len(groups):
            return self._response(state, "拆分后的活动未通过原文或组件校验。")
        state["activity_proposals"] = [item for item in state["activity_proposals"] if item is not proposal] + replacements
        return self._response(state, "活动已拆分为待确认提议。", ui_events=["refresh_activity_cards"])

    def _merge_activity_proposals(self, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        ids = set(payload.get("proposal_ids", []))
        selected = [item for item in state["activity_proposals"] if item["proposal_id"] in ids and item["status"] == "needs_user_confirmation"]
        if len(selected) < 2:
            return self._response(state, "请选择至少两项待确认活动。")
        boundary = {(item["ownership_level"], item["execution_mode"], item["scope"]["coverage"], item["evidence_quote"]) for item in selected}
        if len(boundary) != 1:
            return self._response(state, "责任边界或原文依据不同，不能静默合并。")
        components = {category: list(dict.fromkeys(value for item in selected for value in item["components"][category])) for category in ("actions", "methods", "tools", "techniques", "objects", "artifacts")}
        first = selected[0]
        raw = {"evidence_quote": first["evidence_quote"], "components": components, "ownership_level": first["ownership_level"], "execution_mode": first["execution_mode"], "coverage": first["scope"]["coverage"], "scope_note": first["scope"].get("note")}
        merged = self._validate_activity_proposals([raw], "\n".join(state["raw_user_texts"]), (state.get("extracted_draft") or {}).get("extracted_facts", {}))
        if not merged:
            return self._response(state, "合并后的活动未通过原文或组件校验。")
        state["activity_proposals"] = [item for item in state["activity_proposals"] if item not in selected] + merged
        return self._response(state, "活动已合并为新的待确认提议。", ui_events=["refresh_activity_cards"])

    def _confirm_activity_proposals(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        selected = set(payload.get("proposal_ids", []))
        proposals = [item for item in state["activity_proposals"] if item["status"] == "needs_user_confirmation" and (not selected or item["proposal_id"] in selected)]
        if not proposals:
            return self._response(state, "请至少选择一个待确认的活动提议。")
        if any(item["ownership_level"] == "unknown" or item["execution_mode"] == "unknown" or item["scope"]["coverage"] == "unknown" for item in proposals):
            return self._response(state, "这些活动仍缺少责任或范围确认；请先补充是在指导下、独立还是共同完成，以及完整或部分范围。")
        activities, responsibilities, overrides = [], [], {}
        for proposal in proposals:
            evidence = next((item["evidence_id"] for item in state["evidence_records"] if proposal["evidence_quote"] in item.get("source_text", "")), None)
            if not evidence:
                return self._response(state, "活动提议缺少可追溯的原文证据。")
            activities.append({"activity_id": proposal["activity_id"], "label": "已确认活动", "components": proposal["components"], "evidence_ids": [evidence], "status": "user_confirmed"})
            responsibilities.append({"responsibility_id": proposal["responsibility_id"], "activity_id": proposal["activity_id"], "ownership_level": proposal["ownership_level"], "execution_mode": proposal["execution_mode"], "scope": proposal["scope"], "evidence_ids": [evidence]})
            overrides[proposal["activity_id"]] = {}
            for category, values in proposal["components"].items():
                if values:
                    overrides[proposal["activity_id"]][category] = [evidence]
        updated_payload = {**payload, "canonical_schema_version": "canonical-experience-v2", "activities": activities, "task_responsibilities": responsibilities, "activity_evidence_overrides": overrides}
        response = self._confirm(session_id, state, updated_payload)
        if state.get("confirmed_canonical_experience"):
            for proposal in proposals:
                proposal["status"] = "confirmed"
        return response

    def _confirm(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("extracted_draft")
        if not isinstance(draft, dict):
            return self._response(state, "还没有可确认的事实卡。请先描述经历。")
        result = self.confirmation_gate.confirm_experience(
            experience_draft=draft,
            user_actions={
                "disposition": "accept", "modified_facts": payload.get("modified_facts", {}),
                "new_evidence": payload.get("new_evidence", ""),
                "canonical_schema_version": payload.get("canonical_schema_version", "canonical-experience-v1"),
                "activities": payload.get("activities", []),
                "task_responsibilities": payload.get("task_responsibilities", []),
                "activity_evidence_overrides": payload.get("activity_evidence_overrides", {}),
            },
            evidence_records=state["evidence_records"],
            previous_experience_id=(state.get("confirmed_canonical_experience") or {}).get("experience_id"),
        ).to_dict()
        if not result["canonical_experience"]:
            return self._response(state, "事实仍需补充后才能确认。", pending_question=(result["confirmation_status"].get("validation_errors") or [None])[0])
        old = state.get("confirmed_canonical_experience")
        if old and old != result["canonical_experience"]:
            self.claim_ledger.invalidate_claims_by_experience(session_id, old["experience_id"], "confirmed_fact_changed")
            for claim in state["generated_claims"]:
                if claim["experience_id"] == old["experience_id"]:
                    claim["verification_status"] = "superseded"
        state["confirmed_canonical_experience"] = result["canonical_experience"]
        state["pending_questions"] = []
        state["stage"] = "representative_sample"
        return self._response(state, "事实已确认。请选择目标方向，我会生成候选要点并逐条通过 ClaimGate 审计。", ui_events=["fact_confirmed", "show_role_pack_chips"])

    def _compose(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        canonical = state.get("confirmed_canonical_experience")
        packs = payload.get("role_packs", [])
        if not canonical:
            return self._response(state, "请先确认事实，再生成简历要点。")
        if not isinstance(packs, list) or not packs:
            return self._response(state, "请至少选择一个目标方向。")
        state["selected_role_packs"] = [str(pack) for pack in packs]
        state["stage"] = "composition"
        claims: list[dict[str, Any]] = []
        gates: dict[str, Any] = {}
        for pack in state["selected_role_packs"]:
            for claim in self.bullet_composer.compose_bullets(canonical_experience=canonical, role_pack_name=pack):
                claim_data = claim.to_dict()
                gate = self.claim_gate.validate_claim(bullet_claim=claim_data, canonical_experience=canonical).to_dict()
                claim_data["verification_status"] = gate["status"]
                self.claim_ledger.record_claim(session_id=session_id, bullet_claim=claim_data, gate_status=gate["status"], user_disposition=None)
                claims.append(claim_data)
                gates[claim_data["claim_id"]] = gate
        state["generated_claims"] = claims
        state["claim_gate_results"] = gates
        state["stage"] = "factual_audit"
        return self._response(state, "候选要点已生成并完成 ClaimGate 审计；只有 ready 项会进入右侧预览。", ui_events=["show_bullet_cards", "refresh_resume_preview"])

    def _edit_wording(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        claim_id, wording = str(payload.get("claim_id", "")), str(payload.get("wording", "")).strip()
        canonical = state.get("confirmed_canonical_experience")
        original = next((item for item in state["generated_claims"] if item["claim_id"] == claim_id), None)
        if not canonical or not original or not wording:
            return self._response(state, "请选择一个候选要点并提供新的措辞。")
        edited = deepcopy(original)
        edited["claim_id"] = f"{claim_id}_edit"
        edited["wording"], edited["user_disposition"] = wording, "edited"
        gate = self.claim_gate.validate_claim(bullet_claim=edited, canonical_experience=canonical).to_dict()
        edited["verification_status"] = gate["status"]
        self.claim_ledger.invalidate_claims_by_ids(session_id, [claim_id], "wording_replaced")
        self.claim_ledger.record_claim(session_id=session_id, bullet_claim=edited, gate_status=gate["status"], user_disposition="edited")
        state["generated_claims"] = [item for item in state["generated_claims"] if item["claim_id"] != claim_id] + [edited]
        state["claim_gate_results"][edited["claim_id"]] = gate
        state["claim_user_dispositions"][edited["claim_id"]] = "edited"
        return self._response(state, "已按原确认事实重新审计措辞；未新增事实。", ui_events=["refresh_bullet_card", "refresh_resume_preview"])

    def _rewrite_claim(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        canonical = state.get("confirmed_canonical_experience")
        source_id = str(payload.get("source_claim_id", ""))
        source = next((item for item in state["generated_claims"] if item["claim_id"] == source_id), None)
        tone = str(payload.get("tone", "Conservative"))
        instruction = str(payload.get("instruction", ""))
        if not canonical or canonical.get("schema_version") != "canonical-experience-v2" or not source or source.get("schema_version") != "bullet-claim-v2":
            return self._response(state, "请先选择一条已确认活动生成的 v2 候选要点。")
        if tone not in {"Conservative", "Professional", "High-impact"}:
            return self._response(state, "表达档位必须是 Conservative、Professional 或 High-impact。")
        if self.language_gateway is None:
            return self._response(state, "未配置语言模型；基础的确定性生成与审计仍可使用。")
        model_candidate = self.language_gateway.rewrite_claim(source_claim=source, canonical_experience=canonical, tone=tone, instruction=instruction).rewrite_candidate
        if not isinstance(model_candidate, dict):
            return self._response(state, "模型没有返回可审计的候选措辞。")
        # The model proposes text and traceability only.  It cannot choose an
        # experience, role pack, canonical fact, or audit decision.
        candidate = {
            "schema_version": "bullet-claim-v2", "claim_id": f"claim_{uuid4().hex[:8]}",
            "experience_id": source["experience_id"], "role_pack": source["role_pack"],
            "wording": model_candidate.get("wording", ""),
            "used_facts": model_candidate.get("used_facts", []),
            "dependency_refs": model_candidate.get("dependency_refs", {}),
            "evidence_ids": model_candidate.get("evidence_ids", []),
            "project_responsibility_level": source.get("project_responsibility_level"),
            "omitted_unknowns": source.get("omitted_unknowns", []), "risk_flags": [],
            "verification_status": "candidate", "user_disposition": None,
        }
        gate = self.claim_gate.validate_claim(bullet_claim=candidate, canonical_experience=canonical).to_dict()
        traceability_errors = [
            field for field in ("used_facts", "dependency_refs", "evidence_ids")
            if candidate[field] != source[field]
        ]
        if traceability_errors:
            gate["status"] = "needs_confirmation"
            gate["failed_checks"].append(
                "rewrite_source_traceability: rewrite must preserve source " + ", ".join(traceability_errors)
            )
        candidate["verification_status"] = gate["status"]
        self.claim_ledger.record_claim(session_id=session_id, bullet_claim=candidate, gate_status=gate["status"], user_disposition=None)
        state["generated_claims"].append(candidate)
        state["rewrite_candidates"].append({"claim_id": candidate["claim_id"], "source_claim_id": source_id, "tone": tone, "instruction": instruction, "gate": gate, "selected": False})
        state["claim_gate_results"][candidate["claim_id"]] = gate
        return self._response(state, "已生成新的候选版本并完成 ClaimGate；旧要点未被覆盖。", ui_events=["show_rewrite_candidate", "refresh_resume_preview"])

    def _select_rewrite_candidate(self, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        claim_id = str(payload.get("claim_id", ""))
        for candidate in state["rewrite_candidates"]:
            if candidate["claim_id"] == claim_id:
                candidate["selected"] = True
                state["claim_user_dispositions"][claim_id] = "accepted"
                return self._response(state, "已记录该候选版本为你的选择；其是否显示仍由 ClaimGate 决定。", ui_events=["refresh_resume_preview"])
        return self._response(state, "未找到该候选版本。")

    @staticmethod
    def _allowed_language_intents(stage: str) -> set[str]:
        """Model intent can assist routing only after deterministic intake exists."""
        return {
            "fact_confirmation": {"confirm_facts", "update_facts"},
            "representative_sample": {"update_facts", "select_role_packs"},
            "composition": {"update_facts", "select_role_packs"},
            "factual_audit": {"update_facts", "edit_wording", "accept_bullets"},
            "delivery": {"update_facts", "edit_wording", "accept_bullets"},
        }.get(stage, set())

    @staticmethod
    def _merge_facts(base: dict[str, Any], added: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(base)
        for key, value in added.items():
            if isinstance(value, list):
                merged[key] = list(dict.fromkeys((merged.get(key, []) or []) + value))
            elif isinstance(value, dict):
                current = merged.get(key, {}) or {}
                merged[key] = {**current, **{k: v for k, v in value.items() if v not in (None, "")}}
            elif value not in (None, ""):
                merged[key] = value
        return merged

    def _resume_document(self, session_id: str, state: dict[str, Any]) -> dict[str, Any] | None:
        canonical = state.get("confirmed_canonical_experience")
        if not canonical:
            return None
        valid = {item.claim_id for item in self.claim_ledger.get_valid_claims_for_experience(session_id, canonical["experience_id"]) if item.gate_status == "ready"}
        bullets = [{"claim_id": claim["claim_id"], "text": claim["wording"], "evidence_ids": claim["evidence_ids"]} for claim in state.get("generated_claims", []) if claim["claim_id"] in valid and claim.get("verification_status") == "ready"]
        return {
            "schema_version": "resume-document-v1", "resume_id": session_id,
            "target": {"purpose": "general", "role": ", ".join(state.get("selected_role_packs", [])) or None, "organization": None, "jd_reference": None},
            "basics": {"name": None, "phone": None, "email": None, "location": None, "summary": None, "evidence_ids": []},
            "research_experience": [{
                "item_id": canonical["experience_id"], "organization": "待补充", "title": canonical["role"].get("title") or "已确认经历",
                "department_or_field": canonical["context"].get("domain"), "period": {"start": None, "end": None, "ongoing": False},
                "evidence_ids": canonical["evidence_ids"],
                "bullets": [{"text": item["text"], "evidence_ids": item["evidence_ids"]} for item in bullets],
            }],
            "evidence": [{"evidence_id": item["evidence_id"], "statement": item["source_text"], "source_document_id": None, "source_locator": None, "status": "user_confirmed", "confirmed_at": None} for item in state["evidence_records"]],
            "review_events": [],
        }

    @staticmethod
    def _audit_status(state: dict[str, Any]) -> dict[str, int]:
        gates = state.get("claim_gate_results", {}).values()
        return {"ready": sum(item.get("status") == "ready" for item in gates), "not_ready": sum(item.get("status") != "ready" for item in gates)}

    @staticmethod
    def _response(state: dict[str, Any], message: str, *, pending_question: str | None = None, ui_events: list[str] | None = None) -> dict[str, Any]:
        return {"assistant_message": message, "stage": state["stage"], "pending_question": pending_question, "ui_events": ui_events or [], "resume_patch": None}
