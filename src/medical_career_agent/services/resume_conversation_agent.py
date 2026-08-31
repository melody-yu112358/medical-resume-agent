"""State-aware orchestration for the conversational resume workspace.

This layer deliberately contains no free-form model generation.  It routes user
messages through the existing extraction, confirmation, composition and claim
audit services, and persists the resulting source-of-truth state in sessions.
"""
from __future__ import annotations

import re
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
from .question_guidance import QuestionGuidanceService
from .candidate_profile_intake import CandidateProfileInputError, CandidateProfileIntakeService
from .intake_summary_validation import IntakeSummaryValidationService
from .resume_profile_projection import project_confirmed_profile


STAGES = (
    "intake", "fact_confirmation", "representative_sample", "composition",
    "factual_audit", "delivery",
)
RESUME_TIERS = ("conservative", "professional", "high_impact")
TIER_TONES = {
    "conservative": "Conservative",
    "professional": "Professional",
    "high_impact": "High-impact",
}


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
            "candidate_profile": CandidateProfileIntakeService.initial_state(),
            "raw_user_texts": [], "conversation_turns": [], "extracted_draft": None,
            "confirmed_canonical_experience": None, "evidence_records": [],
            "confirmed_experiences": [], "active_experience_id": None,
            "active_experience_evidence_ids": [],
            "active_experience_identity": None,
            "pending_questions": [], "question_card": None,
            "selected_role_packs": [], "generated_claims": [],
            "representative_sample": None,
            "selected_resume_tier": "professional",
            "claim_gate_results": {}, "claim_user_dispositions": {},
            "activity_proposals": [], "rewrite_candidates": [], "resume_document": None,
            "proposal_audits": [], "language_audit": [],
            "intake_model": {"configured": False, "status": "not_configured", "summary_source": "pending", "summary": None, "error": None},
            "question_history": [],
            "structured_answers": [],
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
        self._refresh_candidate_profile(state)
        self._refresh_question_card(state)
        return {"session_id": session_id, "state": state, "events": payload.get("events", [])}

    def handle_message(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self.read(session_id)
        state = session["state"]
        answer_question_card = deepcopy(state.get("question_card"))
        state["intake_model"]["configured"] = self.language_gateway is not None
        evidence_count_before = len(state.get("evidence_records") or [])
        text = str(payload.get("text", "")).strip()
        action = str(payload.get("action", "")).strip()
        conversation_intent = None
        target_packs = self._role_packs_from_text(text) if not action and state.get("confirmed_canonical_experience") else []
        control_intent = self._safe_control_intent(text) if not action else None
        # Explicit, bounded user controls are safe to recognize deterministically.
        # They must take precedence over an otherwise helpful but actionless model
        # reply; without this, a model can accidentally swallow "确认" or "保研".
        if target_packs:
            # A target direction is workflow input, never experience evidence.
            conversation_intent = "select_role_packs"
        elif control_intent:
            # Explicit questions and workflow controls must not be reclassified as
            # experience evidence even if a model makes an intent error.
            conversation_intent = control_intent
        if text:
            state["raw_user_texts"].append(text)

        if action == "answer_candidate_profile":
            response = self._answer_candidate_profile(state, payload)
        elif action == "confirm_candidate_profile":
            response = self._confirm_candidate_profile(state)
        elif action == "edit_candidate_profile":
            CandidateProfileIntakeService.restart(state["candidate_profile"])
            response = self._response(state, "好的，我们从姓名开始逐项修改；旧答案会保留，提交新答案后覆盖。")
        elif action == "start_new_experience":
            response = self._start_new_experience(state)
        elif action == "select_experience":
            response = self._select_experience(state, payload)
        elif action == "submit_experience":
            response = self._intake(state, payload, text)
        elif action == "confirm_facts":
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
            response = self._supplement_facts(session_id, state, payload, text)
        elif action == "select_role_packs":
            response = self._compose(session_id, state, payload)
        elif action == "approve_representative_sample":
            response = self._approve_representative_sample(session_id, state)
        elif action == "edit_wording":
            response = self._edit_wording(session_id, state, payload)
        elif action == "rewrite_claim":
            response = self._rewrite_claim(session_id, state, payload)
        elif action == "select_rewrite_candidate":
            response = self._select_rewrite_candidate(state, payload)
        elif action == "select_resume_tier":
            response = self._select_resume_tier(state, payload)
        elif action == "accept_bullets":
            ready = [item for item in state.get("generated_claims", []) if item.get("verification_status") == "ready"]
            sample = state.get("representative_sample") or {}
            if not ready:
                response = self._response(state, "尚无可交付的已审计要点；请先确认事实并生成通过审计的内容。")
            elif state.get("stage") != "factual_audit" or sample.get("status") != "approved":
                response = self._response(state, "请先确认代表样板，再生成和审计完整简历。")
            else:
                state["stage"] = "delivery"
                response = self._response(state, "已保存可交付的已审计要点。", ui_events=["delivery_ready"])
        elif conversation_intent == "select_role_packs":
            response = self._compose(session_id, state, {**payload, "role_packs": target_packs})
        elif conversation_intent in {"provide_facts", "correct_facts"}:
            state["stage"] = "fact_confirmation"
            response = self._supplement_facts(session_id, state, payload, text)
        elif conversation_intent == "confirm_facts":
            response = self._confirm_from_conversation(session_id, state, payload)
        elif conversation_intent == "ask_question":
            response = self._explain_current_stage(state)
        elif conversation_intent in {"ask_current_state", "ask_what_to_confirm", "report_ui_problem", "general_help"}:
            response = self._describe_current_state(state)
        elif conversation_intent in {"request_resume_generation", "continue_workflow"}:
            response = self._continue_workflow(session_id, state, payload)
        elif conversation_intent == "rewrite_request":
            response = self._handle_rewrite_request(session_id, state, text)
        elif text and self._contains_extractable_fact(text):
            state["stage"] = "fact_confirmation"
            response = (
                self._intake(state, payload, text)
                if not state.get("extracted_draft")
                else self._supplement_facts(session_id, state, payload, text)
            )
        elif self._pending_activity_proposals(state) and self._looks_like_responsibility_reply(text):
            response = self._apply_responsibility_reply(state, text)
        elif state["stage"] == "intake":
            response = self._intake(state, payload, text)
        elif state["stage"] == "fact_confirmation":
            response = self._route_fact_confirmation_fallback(session_id, state, payload, text)
        else:
            response = self._response(state, "请选择目标方向、确认事实，或提交需要审计的候选措辞。")

        state["resume_document"] = self._resume_document(session_id, state)
        self._refresh_candidate_profile(state)
        self._refresh_question_card(state, response.get("pending_question"))
        if action in {"submit_experience", "update_facts"} and text and len(state.get("evidence_records") or []) > evidence_count_before:
            self._apply_intake_model_summary(state, payload, text, answer_question_card)
        if text:
            state["conversation_turns"].append({"user": text, "assistant": response["assistant_message"], "stage": state["stage"]})
            state["conversation_turns"] = state["conversation_turns"][-12:]
        self.sessions.update(session_id, state=state)
        self.sessions.append_event(session_id, {"type": "conversation_message", "action": action or conversation_intent or "message", "stage": state["stage"]})
        # The browser workspace renders cards from the persisted source of truth,
        # not from a locally reconstructed chat history.
        response["state"] = state
        response["resume_document"] = state["resume_document"]
        response["stage"] = state["stage"]
        response["audit_status"] = self._audit_status(state)
        return response

    def _apply_intake_model_summary(
        self, state: dict[str, Any], payload: dict[str, Any], text: str,
        answer_question_card: dict[str, Any] | None,
    ) -> None:
        allowed_answer_ids = {
            item.get("id") for item in (answer_question_card or {}).get("options", [])
            if isinstance(item, dict)
        }
        selected_option_ids = [
            str(item) for item in (payload.get("selected_option_ids") or [])
            if isinstance(item, str) and item in allowed_answer_ids
        ]
        state["structured_answers"].append({
            "question_id": (answer_question_card or {}).get("question_id"),
            "selected_option_ids": selected_option_ids,
            "free_text": str(payload.get("free_text") or "").strip(),
            "display_text": str(payload.get("display_text") or text).strip(),
        })
        if self.language_gateway is None:
            state["intake_model"] = {
                "configured": False, "status": "not_configured", "summary_source": "pending",
                "summary": None, "fact_refs": [], "evidence_quotes": [],
                "next_question": None, "error": "未配置语言模型；原始回答已保留，但本轮没有 AI 整理。",
            }
            return
        try:
            result = self.language_gateway.summarize_intake_turn(
                text=text,
                selected_option_ids=selected_option_ids,
                free_text=str(payload.get("free_text") or "").strip(),
                session_context=self._conversation_context(state),
                allowed_question_card=deepcopy(state.get("question_card")),
            )
            validated = IntakeSummaryValidationService.validate(
                candidate=result.candidate,
                extracted_facts=(state.get("extracted_draft") or {}).get("extracted_facts", {}),
                evidence_texts=[
                    item.get("source_text", "") for item in state.get("evidence_records", [])
                    if item.get("evidence_id") in set(state.get("active_experience_evidence_ids") or [])
                ],
                question_card=state.get("question_card"),
            )
            validated["configured"] = True
            state["intake_model"] = validated
            next_question = validated.get("next_question")
            if next_question and state.get("question_card"):
                state["question_card"]["recommended_option_ids"] = next_question["recommended_option_ids"]
                question_id = next_question["question_id"]
                if question_id not in state["question_history"]:
                    state["question_history"].append(question_id)
        except Exception as exc:
            state["intake_model"] = {
                "configured": True, "status": "failed", "summary_source": "pending",
                "summary": None, "fact_refs": [], "evidence_quotes": [],
                "next_question": None, "error": "本轮 AI 整理失败；原始回答已保留，可以继续回答后端问题。",
            }
            state["language_audit"].append({"stage": state["stage"], "intake_summary_error": type(exc).__name__})

    @staticmethod
    def _refresh_candidate_profile(state: dict[str, Any]) -> None:
        profile = state.setdefault("candidate_profile", CandidateProfileIntakeService.initial_state())
        profile["current_question"] = CandidateProfileIntakeService.current_question(profile)

    @staticmethod
    def _start_new_experience(state: dict[str, Any]) -> dict[str, Any]:
        if not state.get("confirmed_experiences"):
            return ResumeConversationAgent._response(state, "请先确认当前经历，再添加下一段。")
        if state.get("stage") not in {"intake", "representative_sample"}:
            return ResumeConversationAgent._response(state, "请先完成当前经历的事实确认，再添加下一段。")
        for key, empty in (
            ("extracted_draft", None), ("confirmed_canonical_experience", None),
            ("pending_questions", []), ("question_card", None),
            ("activity_proposals", []), ("proposal_audits", []),
            ("active_experience_evidence_ids", []),
            ("active_experience_identity", None),
        ):
            state[key] = empty
        state["active_experience_id"] = None
        state["stage"] = "intake"
        return ResumeConversationAgent._response(
            state, "已保留前面的已确认经历。现在请描述下一段真实经历。",
            ui_events=["new_experience_started"],
        )

    @staticmethod
    def _select_experience(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        if state.get("stage") != "representative_sample":
            return ResumeConversationAgent._response(state, "请先完成当前经历，再切换已确认经历。")
        experience_id = str(payload.get("experience_id", ""))
        entry = next(
            (item for item in state.get("confirmed_experiences", []) if item.get("experience_id") == experience_id),
            None,
        )
        if not entry:
            return ResumeConversationAgent._response(state, "没有找到这段已确认经历。")
        state["confirmed_canonical_experience"] = deepcopy(entry["canonical_experience"])
        state["extracted_draft"] = deepcopy(entry.get("extracted_draft"))
        state["activity_proposals"] = deepcopy(entry.get("activity_proposals") or [])
        state["active_experience_evidence_ids"] = list(entry.get("evidence_ids") or [])
        state["active_experience_identity"] = deepcopy(
            (entry.get("canonical_experience") or {}).get("identity")
        )
        state["active_experience_id"] = experience_id
        state["pending_questions"] = []
        return ResumeConversationAgent._response(
            state, f"已切换到：{entry.get('label') or '已确认经历'}。",
            ui_events=["experience_selected"],
        )

    @staticmethod
    def _answer_candidate_profile(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        profile = state.setdefault("candidate_profile", CandidateProfileIntakeService.initial_state())
        try:
            CandidateProfileIntakeService.answer(
                profile,
                question_id=str(payload.get("question_id", "")),
                value=payload.get("value"),
                skipped=bool(payload.get("skipped", False)),
            )
        except CandidateProfileInputError as exc:
            return ResumeConversationAgent._response(state, str(exc))
        question = CandidateProfileIntakeService.current_question(profile)
        if question:
            return ResumeConversationAgent._response(state, "已保存。我们继续下一项。", pending_question=question["label"])
        return ResumeConversationAgent._response(
            state, "基础资料和教育背景已经整理好，请确认后再开始采集经历。",
            ui_events=["confirm_candidate_profile"],
        )

    @staticmethod
    def _confirm_candidate_profile(state: dict[str, Any]) -> dict[str, Any]:
        profile = state.setdefault("candidate_profile", CandidateProfileIntakeService.initial_state())
        try:
            CandidateProfileIntakeService.confirm(profile)
        except CandidateProfileInputError as exc:
            return ResumeConversationAgent._response(state, str(exc))
        return ResumeConversationAgent._response(
            state, "资料已确认。现在请告诉我一段最能体现你的真实经历。",
            ui_events=["candidate_profile_confirmed"],
        )

    @staticmethod
    def _refresh_question_card(state: dict[str, Any], pending_question: str | None = None) -> None:
        question = pending_question or next(iter(state.get("pending_questions") or []), None)
        state["question_card"] = QuestionGuidanceService.build(
            question,
            stage=str(state.get("stage", "")),
        )

    @staticmethod
    def _conversation_context(state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("extracted_draft") or {}
        active_ids = set(state.get("active_experience_evidence_ids") or [])
        facts = draft.get("extracted_facts", {})
        return {
            "stage": state.get("stage"), "recent_conversation": state.get("conversation_turns", [])[-6:],
            "pending_questions": state.get("pending_questions", [])[:3],
            "extracted_facts": facts,
            "allowed_fact_refs": sorted(IntakeSummaryValidationService.fact_refs(facts)),
            "active_evidence": [
                {"evidence_id": item.get("evidence_id"), "source_text": item.get("source_text")}
                for item in state.get("evidence_records", [])
                if not active_ids or item.get("evidence_id") in active_ids
                if item.get("kind") != "experience_identity"
            ],
            "confirmed_facts": state.get("confirmed_canonical_experience"),
            "previous_questions": state.get("question_history", []),
            "pending_activities": [{"proposal_id": item.get("proposal_id"), "components": item.get("components"), "ownership_level": item.get("ownership_level"), "execution_mode": item.get("execution_mode"), "coverage": item.get("scope", {}).get("coverage"), "semantic_warnings": item.get("semantic_warnings", [])} for item in state.get("activity_proposals", []) if item.get("status") == "needs_user_confirmation"],
            "selected_role_packs": state.get("selected_role_packs", []),
            "claim_gate_statuses": {key: value.get("status") for key, value in state.get("claim_gate_results", {}).items()},
        }

    def _intake(self, state: dict[str, Any], payload: dict[str, Any], text: str) -> dict[str, Any]:
        if not text:
            return self._response(state, "请用自然语言描述一段真实经历；我会先提取事实，再请你确认。")
        if payload.get("consent_confirmed") is not True:
            return self._response(state, "请先确认这段经历真实准确并同意在本机服务处理后再继续。")
        identity, identity_error = self._normalise_experience_identity(payload.get("experience_identity"))
        if identity_error:
            return self._response(state, identity_error)
        draft = self.experience_drafter.draft(experience_text=text, context_hint=payload.get("context_hint"), consent_confirmed=True).to_dict()
        state["extracted_draft"] = draft
        next_id = f"ev_{len(state['evidence_records']) + 1:03d}"
        state["evidence_records"].append({"evidence_id": next_id, "source_text": text, "status": "confirmed"})
        state["active_experience_evidence_ids"] = [next_id]
        state["active_experience_identity"] = identity
        if identity:
            identity_evidence_id = f"ev_{len(state['evidence_records']) + 1:03d}"
            period = identity["period"]
            period_text = "至今" if period["ongoing"] else (period["end"] or "未填写")
            values = [
                f"经历名称：{identity['project_name']}",
                f"机构或团队：{identity['organization']}" if identity["organization"] else None,
                f"身份或角色：{identity['role_title']}" if identity["role_title"] else None,
                f"经历时间：{period['start'] or '未填写'} 至 {period_text}" if any(period.values()) else None,
            ]
            state["evidence_records"].append({
                "evidence_id": identity_evidence_id,
                "source_text": "；".join(item for item in values if item),
                "status": "confirmed", "kind": "experience_identity",
            })
            state["active_experience_evidence_ids"].append(identity_evidence_id)
            identity["evidence_ids"] = [identity_evidence_id]
        state["pending_questions"] = draft["clarifying_questions"]
        state["stage"] = "fact_confirmation"
        self._propose_activities(state, text, draft["extracted_facts"])
        return self._fact_confirmation_response(state, introduced="我已提取出候选事实")

    def _supplement_facts(
        self, session_id: str, state: dict[str, Any], payload: dict[str, Any], text: str,
    ) -> dict[str, Any]:
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
        state.setdefault("active_experience_evidence_ids", []).append(next_id)
        state["pending_questions"] = merged["clarifying_questions"]
        self._supersede_pending_proposals(state)
        self._invalidate_claims_for_pending_fact_update(session_id, state)
        # Rebuild from all evidence: a later tool/responsibility clarification
        # must not leave the earlier action proposal superseded with no successor.
        self._propose_activities(
            state, self._active_experience_text(state), merged["extracted_facts"],
        )
        return self._fact_confirmation_response(state, introduced="已将补充内容作为待确认事实加入")

    @staticmethod
    def _active_experience_text(state: dict[str, Any]) -> str:
        active_ids = set(state.get("active_experience_evidence_ids") or [])
        return "\n".join(
            item.get("source_text", "") for item in state.get("evidence_records", [])
            if item.get("evidence_id") in active_ids
            and item.get("kind") != "experience_identity"
        )

    @staticmethod
    def _normalise_experience_identity(raw: Any) -> tuple[dict[str, Any] | None, str | None]:
        if raw is None:
            return None, None
        if not isinstance(raw, dict):
            return None, "经历抬头格式不正确，请重新填写。"
        project_name = re.sub(r"\s+", " ", str(raw.get("project_name") or "").strip())
        organization = re.sub(r"\s+", " ", str(raw.get("organization") or "").strip()) or None
        role_title = re.sub(r"\s+", " ", str(raw.get("role_title") or "").strip()) or None
        if not project_name:
            return None, "请填写真实的经历或项目名称；没有正式项目名时可填写研究主题或轮转名称。"
        if len(project_name) > 160 or any(value and len(value) > 120 for value in (organization, role_title)):
            return None, "经历抬头内容过长，请保留正式名称和必要信息。"
        raw_period = raw.get("period") or {}
        if not isinstance(raw_period, dict):
            return None, "经历时间格式不正确，请重新填写。"
        start = str(raw_period.get("start") or "").strip() or None
        ongoing = bool(raw_period.get("ongoing", False))
        end = None if ongoing else (str(raw_period.get("end") or "").strip() or None)
        month_pattern = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
        if any(value and not month_pattern.fullmatch(value) for value in (start, end)):
            return None, "经历时间请使用有效的年月。"
        if start and end and end < start:
            return None, "经历结束时间不能早于开始时间。"
        return {
            "project_name": project_name, "organization": organization,
            "role_title": role_title,
            "period": {"start": start, "end": end, "ongoing": ongoing},
            "evidence_ids": [],
        }, None

    def _fact_confirmation_response(self, state: dict[str, Any], *, introduced: str) -> dict[str, Any]:
        pending = self._pending_activity_proposals(state)
        if pending:
            return self._response(
                state,
                f"{introduced}和 {len(pending)} 项待确认活动卡。请确认、修改、拆分或拒绝；未确认内容不会进入简历。",
                pending_question=(state["pending_questions"] or [None])[0],
                ui_events=["show_fact_card", "show_activity_cards"],
            )
        questions = self._activity_clarification_questions(state)
        state["pending_questions"] = questions
        next_question = questions[0] if questions else "请补充一项可核实的具体工作。"
        return self._response(
            state,
            f"{introduced}，但目前信息还不足以形成活动卡。请先回答：{next_question} 其余缺口会在后续轮次继续询问。",
            pending_question=questions[0] if questions else None,
            ui_events=["show_fact_card", "show_clarification"],
        )

    def _route_fact_confirmation_fallback(self, session_id: str, state: dict[str, Any], payload: dict[str, Any], text: str) -> dict[str, Any]:
        """Safe deterministic fallback when no model intent is available."""
        if self._looks_like_workflow_request(text):
            return self._continue_workflow(session_id, state, payload)
        if self._looks_like_question(text):
            return self._explain_current_stage(state)
        if self._pending_activity_proposals(state) and self._looks_like_responsibility_reply(text):
            return self._apply_responsibility_reply(state, text)
        if self._contains_extractable_fact(text):
            return self._supplement_facts(session_id, state, payload, text)
        return self._response(
            state,
            "我还不能判断这句话是否是在补充经历事实。若要补充，请说明你实际做了什么、用了什么方法或工具，以及范围；也可以直接问我当前需要确认什么。",
            pending_question=(state["pending_questions"] or [None])[0],
        )

    def _continue_workflow(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        if not state.get("confirmed_canonical_experience"):
            if not self._pending_activity_proposals(state):
                response = self._describe_current_state(state)
                response["assistant_message"] = "生成简历前，需要先确认事实和活动责任边界。" + response["assistant_message"]
                return response
            return self._response(
                state,
                "生成简历前，需要先确认事实和活动责任边界。请在事实卡与活动卡中确认、修改或拒绝候选内容；未确认内容不会进入简历。",
                pending_question=(state["pending_questions"] or [None])[0],
                ui_events=["show_fact_card", "show_activity_cards"],
            )
        if state["stage"] in {"representative_sample", "composition"} and not state.get("selected_role_packs"):
            return self._response(state, "事实已确认。请选择至少一个目标方向后，我会先生成一段代表样板。", ui_events=["show_role_pack_chips"])
        if state["stage"] == "representative_sample":
            return self._response(state, "代表样板已经生成。请确认信息密度、语气和责任边界后，再生成完整简历。", ui_events=["show_representative_sample"])
        if state["stage"] == "factual_audit":
            return self._response(state, "候选要点已完成审计；只有 ClaimGate 为 ready 的内容会显示在简历预览中。", ui_events=["show_bullet_cards", "refresh_resume_preview"])
        return self._response(state, "当前工作流已准备好继续。请按页面上的确认或目标方向入口操作。")

    @staticmethod
    def _explain_current_stage(state: dict[str, Any]) -> dict[str, Any]:
        if state["stage"] == "fact_confirmation":
            return ResumeConversationAgent._response(
                state,
                "确认的目的是把你的真实事实、责任边界和原文证据固定下来；之后的简历措辞只能在这些已确认内容内改写，避免把工具、成果或责任写得超过实际情况。",
                pending_question=(state["pending_questions"] or [None])[0],
                ui_events=["show_fact_card", "show_activity_cards"],
            )
        return ResumeConversationAgent._response(state, "我会根据当前阶段解释下一步，但不会把你的问题当作新的经历事实。")

    def _describe_current_state(self, state: dict[str, Any]) -> dict[str, Any]:
        if state["stage"] == "fact_confirmation":
            pending = self._pending_activity_proposals(state)
            if pending:
                return self._response(
                    state,
                    f"当前有 {len(pending)} 项待确认活动卡，同时还需要确认事实卡。确认活动时需要核实做了什么、责任边界、执行方式和范围。",
                    pending_question=(state["pending_questions"] or [None])[0],
                    ui_events=["show_fact_card", "show_activity_cards"],
                )
            questions = self._activity_clarification_questions(state)
            state["pending_questions"] = questions
            return self._response(
                state,
                "当前没有可确认的活动卡；这不是页面遗漏，而是现有信息尚不足以组成一个有具体行动和原文依据的活动。" + " ".join(questions),
                pending_question=questions[0] if questions else None,
                ui_events=["show_fact_card", "show_clarification"],
            )
        if state["stage"] in {"representative_sample", "composition"}:
            if state.get("representative_sample"):
                return self._response(state, "当前只展示一段代表样板；确认样板后才会组合其余经历。", ui_events=["show_representative_sample"])
            return self._response(state, "事实已确认；下一步是选择目标方向并生成一段代表样板。", ui_events=["show_role_pack_chips"])
        if state["stage"] == "factual_audit":
            return self._response(state, "当前在审计阶段；只有 ClaimGate 为 ready 的候选要点会出现在右侧简历预览。", ui_events=["show_bullet_cards", "refresh_resume_preview"])
        return self._response(state, "请先描述一段真实、可核实的经历；我会提取候选事实并说明还需要确认什么。")

    @staticmethod
    def _pending_activity_proposals(state: dict[str, Any]) -> list[dict[str, Any]]:
        return [item for item in state.get("activity_proposals", []) if item.get("status") == "needs_user_confirmation"]

    @staticmethod
    def _activity_clarification_questions(state: dict[str, Any]) -> list[str]:
        facts = (state.get("extracted_draft") or {}).get("extracted_facts", {})
        if facts.get("methods") and not facts.get("actions"):
            return [
                "你具体负责了哪些步骤？",
                "是否做过文献检索、筛选、数据提取或统计分析？",
                "哪些部分是你独立完成，哪些是在指导下或与他人共同完成？",
            ]
        return (state.get("pending_questions") or [
            "你具体做了什么步骤？",
            "使用了什么方法或工具？",
            "哪些部分是独立、在指导下或共同完成的？",
        ])[:3]

    @staticmethod
    def _proposal_gaps(proposal: dict[str, Any]) -> list[str]:
        gaps: list[str] = []
        labels = {
            "ownership_level": "对任务结果的承担",
            "execution_mode": "执行方式",
        }
        for field, label in labels.items():
            if proposal.get(field) == "unknown":
                gaps.append(label)
        if proposal.get("scope", {}).get("coverage") == "unknown":
            gaps.append("完成范围（整个流程还是其中一部分）")
        if proposal.get("semantic_warnings"):
            gaps.append("原文责任表述的核实")
        return gaps

    @staticmethod
    def _activity_label(proposal: dict[str, Any]) -> str:
        labels = {
            "retrieve_literature": "文献检索",
            "screen_studies": "文献筛选",
            "perform_analysis": "R / 数据分析",
        }
        actions = proposal.get("components", {}).get("actions", [])
        return "、".join(labels.get(action, action) for action in actions) or "该活动"

    def _pending_confirmation_response(self, state: dict[str, Any], proposals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        pending = proposals if proposals is not None else self._pending_activity_proposals(state)
        if len(pending) > 1:
            return self._response(
                state,
                f"目前有 {len(pending)} 项待确认活动，请逐项确认或选择其中一项；不能用一次“确认”同时确认不同的责任边界。",
                ui_events=["show_activity_cards"],
            )
        if pending:
            proposal = pending[0]
            gaps = self._proposal_gaps(proposal)
            if gaps:
                detail = "、".join(gaps)
                action = self._activity_label(proposal)
                return self._response(
                    state,
                    f"{action} 已记录的责任信息仍缺少：{detail}。请直接在聊天里说明即可；例如“我负责这个子任务，完成整个既定流程”或“我只完成其中一部分”。",
                    pending_question="请补充该活动是否由你负责，以及完整或部分范围。",
                    ui_events=["show_activity_cards"],
                )
        return self._response(state, "当前没有待确认的活动。")

    def _confirm_from_conversation(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        pending = self._pending_activity_proposals(state)
        if pending:
            if len(pending) != 1 or self._proposal_gaps(pending[0]):
                return self._pending_confirmation_response(state, pending)
            return self._confirm_activity_proposals(session_id, state, {**payload, "proposal_ids": [pending[0]["proposal_id"]]})
        return self._confirm(session_id, state, payload)

    @staticmethod
    def _looks_like_responsibility_reply(text: str) -> bool:
        return any(token in text for token in ("独立", "自己完成", "指导下", "导师指导", "共同完成", "一起完成", "完整流程", "全部完成", "一部分", "部分"))

    def _apply_responsibility_reply(self, state: dict[str, Any], text: str, *, proposal_id: str | None = None, proposed: dict[str, Any] | None = None) -> dict[str, Any]:
        pending = self._pending_activity_proposals(state)
        if proposal_id:
            pending = [item for item in pending if item.get("proposal_id") == proposal_id]
        if len(pending) != 1:
            return self._pending_confirmation_response(state, pending)
        proposal = pending[0]
        evidence_id = f"ev_{len(state['evidence_records']) + 1:03d}"
        state["evidence_records"].append({"evidence_id": evidence_id, "source_text": text, "status": "confirmed"})
        if any(token in text for token in ("独立", "自己完成")):
            proposal["execution_mode"] = "independent"
        elif any(token in text for token in ("指导下", "导师指导")):
            proposal["execution_mode"] = "supervised"
        elif any(token in text for token in ("共同完成", "一起完成")):
            proposal["execution_mode"] = "shared"
        if any(token in text for token in ("完整流程", "全部完成", "完整完成")):
            proposal["scope"]["coverage"] = "full"
        elif any(token in text for token in ("一部分", "部分")):
            proposal["scope"]["coverage"] = "partial"
        if "负责" in text:
            proposal["ownership_level"] = "owned_component"
        if proposed:
            for field, allowed in {
                "ownership_level": {"unknown", "contributed", "owned_component", "led_delivery", "accountable"},
                "execution_mode": {"unknown", "supervised", "independent", "shared"},
            }.items():
                if proposed.get(field) in allowed:
                    proposal[field] = proposed[field]
            if proposed.get("coverage") in {"unknown", "full", "partial"}:
                proposal["scope"]["coverage"] = proposed["coverage"]
        proposal["responsibility_evidence_ids"] = list(dict.fromkeys(proposal.get("responsibility_evidence_ids", []) + [evidence_id]))
        proposal["semantic_warnings"] = [warning for warning in proposal.get("semantic_warnings", []) if not warning.startswith(("execution_mode:", "coverage:"))]
        if self._proposal_gaps(proposal):
            return self._pending_confirmation_response(state, [proposal])
        return self._response(state, "已更新该活动的责任信息；请确认活动卡后写入已确认经历。", ui_events=["refresh_activity_cards"])

    @staticmethod
    def _supersede_pending_proposals(state: dict[str, Any]) -> None:
        for proposal in state.get("activity_proposals", []):
            if proposal.get("status") in {"needs_user_confirmation", "confirmed"}:
                proposal["status"] = "superseded"

    def _invalidate_claims_for_pending_fact_update(self, session_id: str, state: dict[str, Any]) -> None:
        canonical = state.get("confirmed_canonical_experience")
        if not canonical:
            return
        self.claim_ledger.invalidate_claims_by_experience(session_id, canonical["experience_id"], "pending_fact_update")
        for claim in state.get("generated_claims", []):
            if claim.get("experience_id") == canonical["experience_id"]:
                claim["verification_status"] = "superseded"
                if claim.get("claim_id") in state.get("claim_gate_results", {}):
                    state["claim_gate_results"][claim["claim_id"]]["status"] = "superseded"

    def _handle_rewrite_request(self, session_id: str, state: dict[str, Any], text: str) -> dict[str, Any]:
        ready = [claim for claim in state.get("generated_claims", []) if claim.get("verification_status") == "ready"]
        if ready:
            if len(ready) > 1:
                return self._response(state, "有多条已审计要点，请先选择要改写的那一条。", ui_events=["show_bullet_cards"])
            tone = "High-impact" if any(token in text for token in ("力度", "更强")) else "Professional"
            return self._rewrite_claim(session_id, state, {"source_claim_id": ready[0]["claim_id"], "tone": tone, "instruction": text})
        pending = self._pending_activity_proposals(state)
        if pending:
            return self._pending_confirmation_response(state, pending)
        blocked = [result for result in state.get("claim_gate_results", {}).values() if result.get("status") != "ready"]
        if blocked:
            failed = blocked[0].get("failed_checks", [])
            detail = "；".join(failed[:2]) or "候选要点尚未通过 ClaimGate"
            return self._response(state, f"目前没有可改写的 ready 要点：{detail}。请先完成对应事实或责任确认。", ui_events=["show_bullet_cards"])
        return self._response(state, "目前还没有可改写的已审计要点。请先完成事实、活动责任和目标方向确认。")

    def _contains_extractable_fact(self, text: str) -> bool:
        draft = self.experience_drafter.draft(experience_text=text, consent_confirmed=True)
        facts = draft.extracted_facts
        return any(facts.get(category) for category in ("actions", "methods", "tools", "techniques", "objects", "artifacts", "outcomes"))

    @staticmethod
    def _looks_like_question(text: str) -> bool:
        return text.endswith(("?", "？")) or text.strip() in {"什么意思", "这是什么意思", "为什么需要确认", "为什么要确认"}

    @staticmethod
    def _looks_like_workflow_request(text: str) -> bool:
        return text.strip() in {"生成简历", "继续", "下一步", "继续工作流", "开始生成"}

    @classmethod
    def _safe_control_intent(cls, text: str) -> str | None:
        normalized = text.strip()
        if normalized in {"确认", "确认事实", "确认一下"}:
            return "confirm_facts"
        if any(phrase in normalized for phrase in ("专业版措辞", "写得专业一点", "更有力度一点", "专业一点", "更强一点")):
            return "rewrite_request"
        if normalized in {"当前需要确认什么", "我现在还缺什么", "当前状态", "现在到哪一步了"}:
            return "ask_what_to_confirm"
        if normalized in {"我看不到候选卡", "为什么没有卡片", "看不到活动卡", "卡片没有显示"}:
            return "report_ui_problem"
        if normalized in {"下一步做什么", "怎么继续", "如何继续"}:
            return "ask_current_state"
        if cls._looks_like_workflow_request(text):
            return "request_resume_generation"
        if cls._looks_like_question(text):
            return "ask_question"
        return None

    @staticmethod
    def _role_packs_from_text(text: str) -> list[str]:
        """Map common target-language controls to existing role packs only."""
        normalized = text.lower()
        mapping = (
            (("保研", "夏令营", "申博", "科研申请", "academic", "doctoral"), "doctoral_v1"),
            (("临床科研", "医院科研", "clinical research"), "clinical_research_v1"),
            (("临床试验运营", "临床项目协调", "临床试验协调", "临床运营", "clinical operations", "clinical trial coordination", "trial coordination"), "clinical_operations_v1"),
            (("msl", "医学事务", "medical affairs"), "medical_affairs_v1"),
            (("医疗数据", "数字健康", "健康科技", "health data", "digital health"), "health_ai_data_v1"),
        )
        return [role_pack for phrases, role_pack in mapping if any(phrase in normalized for phrase in phrases)]

    def _propose_activities(self, state: dict[str, Any], text: str, facts: dict[str, Any]) -> None:
        candidate = self._deterministic_activity_proposals(text, facts)
        source = "deterministic_intake" if self.language_gateway is not None else "deterministic_fallback"
        candidate = self._enrich_explicit_responsibility(candidate)
        valid, audit = self._validate_activity_proposals_with_audit(candidate, text, facts)
        state["proposal_audits"].append({"source": source, **audit})
        state["activity_proposals"].extend(valid)

    @staticmethod
    def _enrich_explicit_responsibility(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fill only responsibility values stated verbatim in proposal evidence.

        A model may conservatively return ``unknown`` despite an explicit phrase.
        This deterministic enrichment never upgrades an asserted value and never
        infers a fact that is absent from the evidence quote.
        """
        enriched: list[dict[str, Any]] = []
        for proposal in proposals:
            if not isinstance(proposal, dict):
                enriched.append(proposal)
                continue
            item = dict(proposal)
            quote = item.get("evidence_quote")
            if not isinstance(quote, str):
                enriched.append(item)
                continue
            if item.get("ownership_level") == "unknown" and "负责" in quote:
                item["ownership_level"] = "owned_component"
            if item.get("execution_mode") == "unknown":
                if any(token in quote for token in ("独立", "自己完成")):
                    item["execution_mode"] = "independent"
                elif any(token in quote for token in ("指导下", "导师指导", "指导")):
                    item["execution_mode"] = "supervised"
                elif any(token in quote for token in ("共同完成", "一起完成", "协作")):
                    item["execution_mode"] = "shared"
            if item.get("coverage") == "unknown":
                if any(token in quote for token in ("完整流程", "整个既定流程", "全部完成", "完整完成")):
                    item["coverage"] = "full"
                elif any(token in quote for token in ("一部分", "部分步骤", "部分")):
                    item["coverage"] = "partial"
            enriched.append(item)
        return enriched

    @staticmethod
    def _deterministic_activity_proposals(text: str, facts: dict[str, Any]) -> list[dict[str, Any]]:
        """Fallback proposes facts only; it never invents execution or scope."""
        proposals = []
        action_count = len(facts.get("actions", []))
        for action in facts.get("actions", []):
            action_text = text
            execution = "unknown"
            if action == "screen_studies" and "独立" in text:
                execution = "independent"
            elif action == "perform_analysis" and any(token in text for token in ("指导", "带我", "示范")):
                execution = "supervised"
            ownership = "owned_component" if "负责" in text else "unknown"
            coverage = "full" if any(token in text for token in ("完整流程", "整个既定流程", "全部完成", "完整完成")) else "partial" if any(token in text for token in ("一部分", "部分")) else "unknown"
            components = ResumeConversationAgent._components_for_action(action, facts, action_count)
            proposals.append({"evidence_quote": action_text, "components": {"actions": [action], **components}, "ownership_level": ownership, "execution_mode": execution, "coverage": coverage, "scope_note": None})
        return proposals

    @staticmethod
    def _components_for_action(action: str, facts: dict[str, Any], action_count: int) -> dict[str, list[str]]:
        """Conservative action-to-component association for deterministic fallback."""
        all_components = {key: list(facts.get(key, [])) for key in ("methods", "tools", "techniques", "objects", "artifacts")}
        if action_count <= 1:
            return all_components
        if action == "retrieve_literature":
            return {"methods": [], "tools": [tool for tool in all_components["tools"] if tool in {"pubmed", "embase", "cochrane"}], "techniques": [], "objects": [item for item in all_components["objects"] if item == "medical_literature"], "artifacts": []}
        if action == "screen_studies":
            return {"methods": [], "tools": [], "techniques": [], "objects": [item for item in all_components["objects"] if item == "medical_literature"], "artifacts": []}
        if action == "perform_analysis":
            return {"methods": [method for method in all_components["methods"] if method in {"meta_analysis", "sensitivity_analysis", "mendelian_randomization"}], "tools": [tool for tool in all_components["tools"] if tool in {"r", "python", "spss", "stata", "sas", "revman"}], "techniques": all_components["techniques"], "objects": [item for item in all_components["objects"] if item == "research_data"], "artifacts": all_components["artifacts"]}
        return all_components

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
        source = self._active_experience_text(state)
        facts = (state.get("extracted_draft") or {}).get("extracted_facts", {})
        proposals = self._validate_activity_proposals(payload.get("activity_proposals", []), source, facts)
        if not proposals:
            return self._response(state, "修改后的活动提议未通过原文、事实或范围校验。")
        self._supersede_pending_proposals(state)
        state["activity_proposals"].extend(proposals)
        return self._response(state, "已更新活动提议；请确认后写入经历。", ui_events=["refresh_activity_cards"])

    def _split_activity_proposal(self, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        proposal = next((item for item in state["activity_proposals"] if item["proposal_id"] == payload.get("proposal_id") and item["status"] == "needs_user_confirmation"), None)
        groups = payload.get("component_groups", [])
        if not proposal or not isinstance(groups, list) or len(groups) < 2:
            return self._response(state, "请提供至少两个待验证的活动拆分。")
        raw = [{"evidence_quote": proposal["evidence_quote"], "components": group, "ownership_level": proposal["ownership_level"], "execution_mode": proposal["execution_mode"], "coverage": proposal["scope"]["coverage"], "scope_note": proposal["scope"].get("note")} for group in groups]
        replacements = self._validate_activity_proposals(raw, self._active_experience_text(state), (state.get("extracted_draft") or {}).get("extracted_facts", {}))
        if len(replacements) != len(groups):
            return self._response(state, "拆分后的活动未通过原文或组件校验。")
        proposal["status"] = "superseded"
        state["activity_proposals"].extend(replacements)
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
        merged = self._validate_activity_proposals([raw], self._active_experience_text(state), (state.get("extracted_draft") or {}).get("extracted_facts", {}))
        if not merged:
            return self._response(state, "合并后的活动未通过原文或组件校验。")
        for proposal in selected:
            proposal["status"] = "superseded"
        state["activity_proposals"].extend(merged)
        return self._response(state, "活动已合并为新的待确认提议。", ui_events=["refresh_activity_cards"])

    def _confirm_activity_proposals(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        original_proposals = state["activity_proposals"]
        replacements = payload.get("activity_proposals")
        if replacements is not None:
            validated = self._validate_activity_proposals(
                replacements, self._active_experience_text(state),
                (state.get("extracted_draft") or {}).get("extracted_facts", {}),
            )
            if not validated or len(validated) != len(replacements):
                return self._response(state, "修改后的活动提议未通过原文、事实或范围校验。")
            state["activity_proposals"] = validated
        selected = set(payload.get("proposal_ids", []))
        proposals = [item for item in state["activity_proposals"] if item["status"] == "needs_user_confirmation" and (not selected or item["proposal_id"] in selected)]
        if not proposals:
            state["activity_proposals"] = original_proposals
            return self._response(state, "请至少选择一个待确认的活动提议。")
        if any(item["ownership_level"] == "unknown" or item["execution_mode"] == "unknown" or item["scope"]["coverage"] == "unknown" for item in proposals):
            state["activity_proposals"] = original_proposals
            return self._response(state, "这些活动仍缺少责任或范围确认；请先补充是在指导下、独立还是共同完成，以及完整或部分范围。")
        activities, responsibilities, overrides = [], [], {}
        active_evidence_ids = set(state.get("active_experience_evidence_ids") or [])
        for proposal in proposals:
            evidence_ids = [
                item["evidence_id"] for item in state["evidence_records"]
                if item.get("evidence_id") in active_evidence_ids
                and (
                    proposal["evidence_quote"] in item.get("source_text", "")
                    or item.get("source_text", "") in proposal["evidence_quote"]
                )
            ]
            if not evidence_ids:
                state["activity_proposals"] = original_proposals
                return self._response(state, "活动提议缺少可追溯的原文证据。")
            activities.append({"activity_id": proposal["activity_id"], "label": "已确认活动", "components": proposal["components"], "evidence_ids": evidence_ids, "status": "user_confirmed"})
            responsibility_evidence = list(dict.fromkeys(evidence_ids + proposal.get("responsibility_evidence_ids", [])))
            responsibilities.append({"responsibility_id": proposal["responsibility_id"], "activity_id": proposal["activity_id"], "ownership_level": proposal["ownership_level"], "execution_mode": proposal["execution_mode"], "scope": proposal["scope"], "evidence_ids": responsibility_evidence})
            overrides[proposal["activity_id"]] = {}
            for category, values in proposal["components"].items():
                if values:
                    overrides[proposal["activity_id"]][category] = evidence_ids
        updated_payload = {**payload, "canonical_schema_version": "canonical-experience-v2", "activities": activities, "task_responsibilities": responsibilities, "activity_evidence_overrides": overrides}
        for proposal in proposals:
            proposal["status"] = "confirmed"
        response = self._confirm(session_id, state, updated_payload)
        if not state.get("confirmed_canonical_experience"):
            state["activity_proposals"] = original_proposals
        return response

    def _confirm(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("extracted_draft")
        if not isinstance(draft, dict):
            return self._response(state, "还没有可确认的事实卡。请先描述经历。")
        active_evidence_ids = set(state.get("active_experience_evidence_ids") or [])
        active_evidence_records = [
            item for item in state["evidence_records"]
            if not active_evidence_ids or item.get("evidence_id") in active_evidence_ids
        ]
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
            evidence_records=active_evidence_records,
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
        canonical = result["canonical_experience"]
        if state.get("active_experience_identity"):
            canonical["identity"] = deepcopy(state["active_experience_identity"])
        state["confirmed_canonical_experience"] = canonical
        state["pending_questions"] = []
        self._upsert_confirmed_experience(state)
        pending = self._pending_activity_proposals(state)
        if pending:
            state["stage"] = "fact_confirmation"
            return self._response(
                state,
                "事实卡已确认，但活动责任边界仍待确认；完成这些活动后才能生成简历要点。",
                pending_question=(state["pending_questions"] or [None])[0],
                ui_events=["fact_confirmed", "show_activity_cards"],
            )
        state["stage"] = "representative_sample"
        return self._response(state, "事实已确认。请选择目标方向，我会生成候选要点并逐条通过 ClaimGate 审计。", ui_events=["fact_confirmed", "show_role_pack_chips"])

    @staticmethod
    def _upsert_confirmed_experience(state: dict[str, Any]) -> None:
        canonical = state.get("confirmed_canonical_experience")
        if not canonical:
            return
        experience_id = canonical["experience_id"]
        context = canonical.get("context") or {}
        role = canonical.get("role") or {}
        identity = canonical.get("identity") or {}
        label = identity.get("project_name") or " · ".join(
            value for value in (context.get("domain"), role.get("title"))
            if isinstance(value, str) and value.strip()
        ) or f"已确认经历 {len(state.get('confirmed_experiences', [])) + 1}"
        entry = {
            "experience_id": experience_id,
            "label": label,
            "canonical_experience": deepcopy(canonical),
            "extracted_draft": deepcopy(state.get("extracted_draft")),
            "activity_proposals": deepcopy(state.get("activity_proposals") or []),
            "evidence_ids": list(state.get("active_experience_evidence_ids") or canonical.get("evidence_ids") or []),
        }
        experiences = state.setdefault("confirmed_experiences", [])
        active_experience_id = state.get("active_experience_id")
        index = next((
            index for index, item in enumerate(experiences)
            if item.get("experience_id") in {experience_id, active_experience_id}
        ), None)
        if index is None:
            experiences.append(entry)
        else:
            experiences[index] = entry
        state["active_experience_id"] = experience_id

    @staticmethod
    def _confirmed_canonicals(state: dict[str, Any]) -> list[dict[str, Any]]:
        canonicals = [
            item.get("canonical_experience") for item in state.get("confirmed_experiences", [])
            if isinstance(item.get("canonical_experience"), dict)
        ]
        current = state.get("confirmed_canonical_experience")
        if current and not any(item.get("experience_id") == current.get("experience_id") for item in canonicals):
            canonicals.append(current)
        return canonicals

    @classmethod
    def _canonical_for_claim(
        cls, state: dict[str, Any], claim: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        experience_id = (claim or {}).get("experience_id")
        return next(
            (
                canonical for canonical in cls._confirmed_canonicals(state)
                if canonical.get("experience_id") == experience_id
            ),
            None,
        )

    def _compose(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        canonicals = self._confirmed_canonicals(state)
        packs = payload.get("role_packs", [])
        if not canonicals:
            return self._response(state, "请先确认事实，再生成简历要点。")
        if self._pending_activity_proposals(state):
            return self._pending_confirmation_response(state)
        if not isinstance(packs, list) or not packs:
            return self._response(state, "请至少选择一个目标方向。")
        old_claim_ids = [item.get("claim_id") for item in state.get("generated_claims", []) if item.get("claim_id")]
        if old_claim_ids:
            self.claim_ledger.invalidate_claims_by_ids(
                session_id, old_claim_ids, "representative_sample_replaced",
            )
        state["selected_role_packs"] = [str(pack) for pack in packs]
        state["selected_resume_tier"] = "professional"
        state["rewrite_candidates"] = []
        flagship = max(canonicals, key=self._representative_sample_score)
        claims, gates = self._compose_claims(
            session_id, [flagship], state["selected_role_packs"],
        )
        state["generated_claims"] = claims
        state["claim_gate_results"] = gates
        state["representative_sample"] = {
            "experience_id": flagship["experience_id"], "status": "pending",
        }
        state["stage"] = "representative_sample"
        return self._response(
            state,
            "已生成一段代表样板并完成 ClaimGate 审计。请先确认信息密度、语气和责任边界；批准后才会组合全部经历。",
            ui_events=["show_representative_sample", "refresh_resume_preview"],
        )

    @staticmethod
    def _representative_sample_score(canonical: dict[str, Any]) -> tuple[int, int, int]:
        return (
            len(canonical.get("task_responsibilities") or []),
            len(canonical.get("activities") or []),
            len(canonical.get("evidence_ids") or []),
        )

    def _compose_claims(
        self, session_id: str, canonicals: list[dict[str, Any]], packs: list[str],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        claims: list[dict[str, Any]] = []
        gates: dict[str, Any] = {}
        for canonical in canonicals:
            for pack in packs:
                for claim in self.bullet_composer.compose_bullets(canonical_experience=canonical, role_pack_name=pack):
                    claim_data = claim.to_dict()
                    gate = self.claim_gate.validate_claim(bullet_claim=claim_data, canonical_experience=canonical).to_dict()
                    claim_data["verification_status"] = gate["status"]
                    self.claim_ledger.record_claim(session_id=session_id, bullet_claim=claim_data, gate_status=gate["status"], user_disposition=None)
                    claims.append(claim_data)
                    gates[claim_data["claim_id"]] = gate
        return claims, gates

    def _approve_representative_sample(
        self, session_id: str, state: dict[str, Any],
    ) -> dict[str, Any]:
        sample = state.get("representative_sample") or {}
        if state.get("stage") != "representative_sample" or sample.get("status") != "pending":
            return self._response(state, "当前没有待确认的代表样板。")
        rewrite_ids = {
            item.get("claim_id") for item in state.get("rewrite_candidates", [])
        }
        sample_claims = [
            claim for claim in state.get("generated_claims", [])
            if claim.get("experience_id") == sample.get("experience_id")
            and claim.get("claim_id") not in rewrite_ids
        ]
        if not sample_claims or any(
            state.get("claim_gate_results", {}).get(claim.get("claim_id"), {}).get("status") != "ready"
            for claim in sample_claims
        ):
            return self._response(state, "代表样板仍有未通过事实审计的要点，请修改或补充事实后再确认。")
        sample["status"] = "approved"
        state["stage"] = "composition"
        remaining = [
            canonical for canonical in self._confirmed_canonicals(state)
            if canonical.get("experience_id") != sample.get("experience_id")
        ]
        claims, gates = self._compose_claims(
            session_id, remaining, state.get("selected_role_packs", []),
        )
        state["generated_claims"].extend(claims)
        state["claim_gate_results"].update(gates)
        state["stage"] = "factual_audit"
        return self._response(
            state,
            "代表样板已冻结；其余经历已按同一标准组合并完成 ClaimGate 审计。只有 ready 项会进入预览。",
            ui_events=["sample_approved", "show_bullet_cards", "refresh_resume_preview"],
        )

    def _edit_wording(self, session_id: str, state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        claim_id, wording = str(payload.get("claim_id", "")), str(payload.get("wording", "")).strip()
        original = next((item for item in state["generated_claims"] if item["claim_id"] == claim_id), None)
        canonical = self._canonical_for_claim(state, original)
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
        source_id = str(payload.get("source_claim_id", ""))
        source = next((item for item in state["generated_claims"] if item["claim_id"] == source_id), None)
        canonical = self._canonical_for_claim(state, source)
        tone = str(payload.get("tone", "Conservative"))
        instruction = str(payload.get("instruction", ""))
        if any(item.get("claim_id") == source_id for item in state.get("rewrite_candidates", [])):
            return self._response(state, "请从基础要点创建档位版本，避免对候选改写再次改写。")
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
                if candidate.get("gate", {}).get("status") != "ready":
                    return self._response(state, "这版措辞尚未通过 ClaimGate，因此不能用于简历预览。")
                source_id = candidate.get("source_claim_id")
                tone = candidate.get("tone")
                for other in state["rewrite_candidates"]:
                    if other.get("source_claim_id") == source_id and other.get("tone") == tone:
                        other["selected"] = other.get("claim_id") == claim_id
                candidate["selected"] = True
                state["selected_resume_tier"] = self._tier_for_tone(str(tone))
                state["claim_user_dispositions"][claim_id] = "accepted"
                return self._response(state, "已应用到对应档位；右侧预览已切换到该已审计版本。", ui_events=["refresh_resume_preview"])
        return self._response(state, "未找到该候选版本。")

    @staticmethod
    def _tier_for_tone(tone: str) -> str:
        return next((tier for tier, value in TIER_TONES.items() if value == tone), "professional")

    @staticmethod
    def _select_resume_tier(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        tier = str(payload.get("tier", ""))
        if tier not in RESUME_TIERS:
            return ResumeConversationAgent._response(state, "请选择稳妥版、专业版或高竞争力版。")
        if not state.get("generated_claims"):
            return ResumeConversationAgent._response(state, "请先生成并审计简历要点，再切换表达档位。")
        state["selected_resume_tier"] = tier
        return ResumeConversationAgent._response(
            state, "已切换简历表达档位；事实、证据和责任边界保持不变。",
            ui_events=["refresh_resume_preview"],
        )

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

    def resume_tier_documents(
        self, session_id: str, state: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any] | None]:
        source_state = state if state is not None else self.read(session_id)["state"]
        return {tier: self._resume_document(session_id, source_state, tier=tier) for tier in RESUME_TIERS}

    def _resume_document(
        self, session_id: str, state: dict[str, Any], *, tier: str | None = None,
    ) -> dict[str, Any] | None:
        canonicals = self._confirmed_canonicals(state)
        if not canonicals:
            return None
        selected_tier = tier if tier in RESUME_TIERS else state.get("selected_resume_tier", "professional")
        selected_tone = TIER_TONES.get(str(selected_tier), "Professional")
        valid = {
            item.claim_id
            for canonical in canonicals
            for item in self.claim_ledger.get_valid_claims_for_experience(session_id, canonical["experience_id"])
            if item.gate_status == "ready"
        }
        selected_rewrites = {
            item["source_claim_id"]: item["claim_id"]
            for item in state.get("rewrite_candidates", [])
            if item.get("selected") and item.get("tone") == selected_tone
            and item.get("gate", {}).get("status") == "ready"
        }
        rewrite_source_by_id = {
            item["claim_id"]: item.get("source_claim_id")
            for item in state.get("rewrite_candidates", [])
        }
        bullets_by_experience: dict[str, list[dict[str, Any]]] = {
            canonical["experience_id"]: [] for canonical in canonicals
        }
        for claim in state.get("generated_claims", []):
            claim_id = claim.get("claim_id")
            if claim_id not in valid or claim.get("verification_status") != "ready":
                continue
            source_id = rewrite_source_by_id.get(claim_id)
            if source_id:
                if selected_rewrites.get(source_id) != claim_id:
                    continue
            elif claim_id in selected_rewrites:
                # A selected rewrite replaces its source in the rendered resume,
                # while both versions remain in the audit ledger.
                continue
            experience_id = claim.get("experience_id")
            if experience_id in bullets_by_experience:
                bullets_by_experience[experience_id].append({
                    "claim_id": claim_id, "text": claim["wording"],
                    "evidence_ids": claim["evidence_ids"],
                })
        basics, education, profile_evidence = CandidateProfileIntakeService.document_sections(
            state.get("candidate_profile") or {}
        )
        profile_projection = project_confirmed_profile(canonicals)
        basics["summary"] = profile_projection["summary"]
        basics["evidence_ids"] = sorted(set(basics.get("evidence_ids", [])) | set(profile_projection["summary_evidence_ids"]))
        return {
            "schema_version": "resume-document-v1", "resume_id": session_id,
            "target": {"purpose": "general", "role": ", ".join(state.get("selected_role_packs", [])) or None, "organization": None, "jd_reference": None},
            "basics": basics,
            "education": education,
            "skills": profile_projection["skills"],
            "research_experience": [{
                "item_id": canonical["experience_id"],
                "project_name": (canonical.get("identity") or {}).get("project_name"),
                "organization": (canonical.get("identity") or {}).get("organization") or "",
                "title": (canonical.get("identity") or {}).get("role_title") or canonical["role"].get("title") or "",
                "department_or_field": canonical["context"].get("topic"),
                "period": deepcopy((canonical.get("identity") or {}).get("period") or {"start": None, "end": None, "ongoing": False}),
                "evidence_ids": canonical["evidence_ids"],
                "bullets": [
                    {"text": item["text"], "evidence_ids": item["evidence_ids"]}
                    for item in bullets_by_experience[canonical["experience_id"]]
                ],
            } for canonical in canonicals],
            "evidence": profile_evidence + [{"evidence_id": item["evidence_id"], "statement": item["source_text"], "source_document_id": None, "source_locator": None, "status": "user_confirmed", "confirmed_at": None} for item in state["evidence_records"]],
            "review_events": [],
        }

    @staticmethod
    def _audit_status(state: dict[str, Any]) -> dict[str, int]:
        gates = state.get("claim_gate_results", {}).values()
        return {"ready": sum(item.get("status") == "ready" for item in gates), "not_ready": sum(item.get("status") != "ready" for item in gates)}

    @staticmethod
    def _response(state: dict[str, Any], message: str, *, pending_question: str | None = None, ui_events: list[str] | None = None) -> dict[str, Any]:
        return {"assistant_message": message, "stage": state["stage"], "pending_question": pending_question, "ui_events": ui_events or [], "resume_patch": None}
