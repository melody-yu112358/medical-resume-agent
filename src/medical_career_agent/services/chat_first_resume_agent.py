"""Independent chat-first v2 PoC.

This deliberately does not reuse the stage-first conversation agent.  The model
plans a turn; deterministic services remain the only way to persist facts,
canonical experience, claims, and the preview document.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any
from uuid import uuid4

from ..adapters.file_session_store import FileSessionStore
from ..ports.repositories import ModelGateway
from .bullet_composer import BulletComposerService
from .claim_gate import ClaimGateService
from .claim_ledger import ClaimLedgerService
from .confirmation_gate import ConfirmationGateService
from .conversation_model_gateway import ModelGatewayConversationGateway
from .experience_draft import ExperienceDraftService
from .presentation_writer import PresentationWriterService


class ChatFirstResumeAgent:
    """Small v2 PoC: LLM-first understanding, deterministic commit."""

    _ACTIONS = {"propose_fact", "propose_activity", "propose_responsibility", "select_target", "compose_sample", "rewrite_claim"}
    _PACKS = {"doctoral_v1", "clinical_research_v1", "medical_affairs_v1", "health_ai_data_v1"}

    def __init__(self, *, sessions: FileSessionStore, experience_drafter: ExperienceDraftService,
                 confirmation_gate: ConfirmationGateService, bullet_composer: BulletComposerService,
                 claim_gate: ClaimGateService, claim_ledger: ClaimLedgerService,
                 model_gateway: ModelGateway | None = None) -> None:
        self.sessions, self.experience_drafter, self.confirmation_gate = sessions, experience_drafter, confirmation_gate
        self.bullet_composer, self.claim_gate, self.claim_ledger = bullet_composer, claim_gate, claim_ledger
        self.model_gateway = model_gateway
        self.rewriter = ModelGatewayConversationGateway(model_gateway) if model_gateway else None
        self.presentation_writer = PresentationWriterService(model_gateway)

    @staticmethod
    def initial_state() -> dict[str, Any]:
        return {"conversation_version": "chat-first-v2", "messages": [], "raw_user_texts": [],
                "evidence_records": [], "draft": None, "activities": [], "task_responsibilities": [],
                "canonical_experience": None, "pending_confirmation": None, "selected_target": None,
                "claims": [], "claim_gate_results": {}, "rewrite_candidates": [], "presentation": None, "audit": []}

    def create(self) -> dict[str, Any]:
        session_id = self.sessions.create()
        self.sessions.update(session_id, state=self.initial_state())
        return self.read(session_id)

    def read(self, session_id: str) -> dict[str, Any]:
        raw = self.sessions.get(session_id); state = self.initial_state(); state.update(raw.get("state", {}))
        return {"session_id": session_id, "state": state, "resume_document": self._document(session_id, state)}

    def handle(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.read(session_id); state = current["state"]; text = str(payload.get("text", "")).strip()
        turn_id = f"turn_{uuid4().hex[:12]}"
        plan, trace = self._plan(text, state, turn_id)
        state["audit"].append({"turn_id": turn_id, "turn_plan": plan, "runtime_trace": trace})
        if text: state["raw_user_texts"].append(text)
        message, confirmation = self._apply(session_id, state, text, plan, payload.get("consent_confirmed") is True)
        writer_trace = state.pop("_runtime_presentation_trace", None)
        trace["presentation_writer_called"] = writer_trace is not None
        if writer_trace:
            trace["presentation_writer_status"] = writer_trace["status"]
            trace["presentation_validation_status"] = writer_trace["validation_status"]
            if writer_trace.get("error"):
                trace["presentation_writer_error"] = writer_trace["error"]
            trace["final_response_source"] = "presentation"
        elif plan.get("assistant_message") and message == plan["assistant_message"]:
            trace["final_response_source"] = "model/free_chat"
        else:
            trace["final_response_source"] = "deterministic"
        trace["fallback_used"] = trace["model_plan_status"] != "success" or message.startswith("请直接描述一段真实经历")
        state["messages"].append({"role": "user", "text": text})
        state["messages"].append({"role": "assistant", "text": message})
        self.sessions.update(session_id, state=state)
        self.sessions.append_event(session_id, {"type": "conversation_v2", "turn_id": turn_id, "runtime_trace": trace})
        document = self._document(session_id, state)
        return {"session_id": session_id, "assistant_message": message, "confirmation": confirmation,
                "needs_user_reply": plan["needs_user_reply"], "resume_document": document,
                "audit_status": self._audit(state), "runtime_trace": trace, "state": state}

    def _plan(self, text: str, state: dict[str, Any], turn_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        fallback = {"assistant_message": None, "proposed_actions": [], "confirmation": None, "needs_user_reply": False}
        trace: dict[str, Any] = {"turn_id": turn_id, "model_plan_called": False, "model_plan_status": "not_configured" if not self.model_gateway else "not_called", "proposed_action_types": [], "fallback_used": False, "presentation_writer_called": False, "presentation_writer_status": "not_called", "presentation_validation_status": "not_called", "final_response_source": "deterministic"}
        if not self.model_gateway or not text: return fallback, trace
        trace["model_plan_called"] = True
        context = {"recent_messages": state["messages"][-8:], "has_canonical": bool(state["canonical_experience"]),
                   "pending_confirmation": state["pending_confirmation"], "target": state["selected_target"],
                   "confirmed_facts": (state.get("draft") or {}).get("extracted_facts", {})}
        try:
            raw = self.model_gateway.generate(task="chat_first_resume_v2_turn", context={
                "instruction": "Return JSON only: assistant_message, proposed_actions, confirmation, needs_user_reply. You are a natural Chinese resume conversation partner. Actions are untrusted proposals only. Allowed types: propose_fact, propose_activity, propose_responsibility, select_target, compose_sample, rewrite_claim. For ordinary questions such as ‘这是什么意思’, ‘这句不像简历’, or ‘能更自然一点吗’, answer naturally with proposed_actions: [] and do not invent an update. For a request to combine current ready material into one complete sentence (for example ‘给我完整的一句话’ or ‘不要那么碎’), emit compose_sample; for a full-sentence rewrite emit compose_sample, not a fact action. Never mutate canonical facts, claims, audit, or session. Preserve evidence boundaries; ask at most one concise question when responsibility/scope is missing. Do not mention internal stages or schemas.",
                "user_text": text, "session_context": context,
                "response_shape": {"assistant_message": "natural Chinese", "proposed_actions": [{"type": "propose_fact", "evidence_quote": "verbatim user substring"}], "confirmation": None, "needs_user_reply": True}})
            value = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I | re.S))
            if not isinstance(value, dict):
                trace.update({"model_plan_status": "error", "model_plan_error": "ModelOutputError: expected JSON object"})
                return fallback, trace
            actions = [a for a in value.get("proposed_actions", []) if isinstance(a, dict) and a.get("type") in self._ACTIONS]
            trace.update({"model_plan_status": "success", "proposed_action_types": [str(a.get("type")) for a in actions]})
            return {"assistant_message": value.get("assistant_message") if isinstance(value.get("assistant_message"), str) else None,
                    "proposed_actions": actions, "confirmation": value.get("confirmation"), "needs_user_reply": value.get("needs_user_reply") is True}, trace
        except Exception as exc:
            trace.update({"model_plan_status": "error", "model_plan_error": self._safe_error(exc)})
            return fallback, trace

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        message = str(exc).replace("\n", " ").strip()
        return f"{type(exc).__name__}: {message[:160]}" if message else type(exc).__name__

    def _apply(self, session_id: str, state: dict[str, Any], text: str, plan: dict[str, Any], consent: bool) -> tuple[str, dict[str, Any] | None]:
        target = self._target(text, plan)
        # “按保研方向写得专业一点” is a rewrite of the current claim, not
        # another generic compose turn.  A target in the same sentence only
        # selects the role pack before rewriting when one has not been chosen.
        presentation_requested = any(action.get("type") == "compose_sample" for action in plan["proposed_actions"])
        if (self._is_rewrite(text, plan) or presentation_requested) and state.get("canonical_experience"):
            if target and target != state.get("selected_target"):
                self._compose(session_id, state, target)
            elif not state.get("claims") and state.get("selected_target"):
                self._compose(session_id, state, state["selected_target"])
            return self._present(state, text), None
        if target and state.get("canonical_experience"):
            self._compose(session_id, state, target)
            return self._present(state, ""), None
        if text in {"确认", "好的，确认", "确认一下"} and state.get("pending_confirmation"):
            if self._commit(session_id, state):
                return "我已确认目前这部分真实经历。告诉我目标方向（如保研、临床科研、MSL），我会立即给出第一版。", None
        if self._is_correction(text, state):
            return self._correct(session_id, state, text)
        if text and self._has_facts(text):
            if not consent:
                return "请先勾选真实性确认，我才会把这段内容作为本机证据处理。", None
            self._ingest(state, text)
            if self._ready_to_commit(state):
                self._commit(session_id, state)
                return (plan.get("assistant_message") or "我已理解并确认这部分经历。你想按保研、临床科研、MSL 还是医疗数据方向来写？"), None
            confirmation = self._light_confirmation(state)
            return (plan.get("assistant_message") or confirmation["question"]), confirmation
        if state.get("pending_confirmation") and text:
            self._update_pending_responsibility(state, text)
            if self._ready_to_commit(state) and self._commit(session_id, state):
                return "这部分经历已确认。现在告诉我目标方向，我会马上生成第一版措辞。", None
            confirmation = self._light_confirmation(state)
            return confirmation["question"], confirmation
        return (plan.get("assistant_message") or "请直接描述一段真实经历；我会用已有信息自然追问，并尽快给出第一版措辞。"), None

    @staticmethod
    def _has_facts(text: str) -> bool:
        return any(token in text.lower() for token in ("r", "pubmed", "meta", "分析", "筛选", "检索", "数据提取", "qPCR", "文献"))

    def _ingest(self, state: dict[str, Any], text: str) -> None:
        parsed = self.experience_drafter.draft(experience_text=text, consent_confirmed=True).to_dict()
        prior = state.get("draft") or {"extracted_facts": {}}
        facts = deepcopy(prior.get("extracted_facts", {}))
        for key, value in parsed["extracted_facts"].items():
            if isinstance(value, list): facts[key] = list(dict.fromkeys((facts.get(key) or []) + value))
            elif isinstance(value, dict): facts[key] = {**(facts.get(key) or {}), **value}
            else: facts[key] = value
        state["draft"] = {"extracted_facts": facts, "unknown_items": parsed.get("unknown_items", [])}
        state["evidence_records"].append({"evidence_id": f"ev_{len(state['evidence_records'])+1:03d}", "source_text": text, "status": "confirmed"})
        # PubMed + 检索 is a real retrieval activity even if the raw wording
        # does not happen to say the exact extractor phrase “文献检索”.
        if "pubmed" in facts.get("tools", []) and "检索" in text and "retrieve_literature" not in facts.get("actions", []):
            facts["actions"].append("retrieve_literature")
        state["activities"], state["task_responsibilities"] = self._activities(
            facts, "\n".join(state["raw_user_texts"]), state.get("activities", []), state.get("task_responsibilities", []),
        )
        state["pending_confirmation"] = self._light_confirmation(state) if not self._ready_to_commit(state) else None

    def _activities(self, facts: dict[str, Any], evidence: str, prior_activities: list[dict[str, Any]], prior_responsibilities: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        activities, responsibilities = [], []
        previous_by_action = {tuple(item.get("components", {}).get("actions", [])): item for item in prior_activities}
        previous_responsibilities = {item.get("activity_id"): item for item in prior_responsibilities}
        for action in facts.get("actions", []):
            previous = previous_by_action.get((action,), {})
            activity_id = previous.get("activity_id", f"act_{uuid4().hex[:8]}")
            components = {"actions": [action], "methods": [], "tools": [], "techniques": [], "objects": [], "artifacts": []}
            if action == "perform_analysis": components["methods"] = [x for x in facts.get("methods", []) if x in {"meta_analysis", "sensitivity_analysis"}]; components["tools"] = [x for x in facts.get("tools", []) if x == "r"]
            elif action == "retrieve_literature": components["tools"] = [x for x in facts.get("tools", []) if x == "pubmed"]; components["objects"] = [x for x in facts.get("objects", []) if x == "medical_literature"]
            elif action == "extract_data": components["objects"] = [x for x in facts.get("objects", []) if x in {"research_data", "medical_literature"}]
            segment = self._activity_segment(action, evidence)
            ownership = "owned_component" if any(word in segment for word in ("负责", "主要是我", "我自己")) else "contributed"
            execution = self._execution_from_text(segment)
            coverage = self._coverage_from_text(segment)
            previous_responsibility = previous_responsibilities.get(activity_id, {})
            # A generic later confirmation such as “都完成了完整流程” fills
            # only a missing field; it must never overwrite a task-specific
            # responsibility already stated in the original sentence.
            execution = execution or previous_responsibility.get("execution_mode")
            coverage = coverage or (previous_responsibility.get("scope") or {}).get("coverage")
            complete = bool(execution and coverage)
            activities.append({"activity_id": activity_id, "label": "", "components": components, "evidence_ids": [], "status": "confirmed" if complete else "needs_user_confirmation"})
            responsibilities.append({"responsibility_id": previous_responsibility.get("responsibility_id", f"resp_{uuid4().hex[:8]}"), "activity_id": activity_id, "ownership_level": ownership, "execution_mode": execution, "scope": {"coverage": coverage, "note": None}, "evidence_ids": []})
        return activities, responsibilities

    @staticmethod
    def _activity_segment(action: str, evidence: str) -> str:
        """Select the clause that actually describes this atomic activity."""
        markers = {
            "retrieve_literature": ("pubmed", "检索", "文献检索"),
            "screen_studies": ("筛选",),
            "extract_data": ("数据提取", "提取数据"),
            "perform_analysis": ("r 分析", "r分析", "meta 分析", "meta分析", "数据分析", "跑数据"),
        }
        clauses = [clause.strip() for clause in re.split(r"[，。；;\n]", evidence) if clause.strip()]
        relevant = [clause for clause in clauses if any(marker in clause.lower() for marker in markers.get(action, ()))]
        return relevant[-1] if relevant else evidence

    @staticmethod
    def _execution_from_text(text: str) -> str | None:
        mentions = [(text.rfind(token), value) for token, value in (("独立", "independent"), ("自己做", "independent"), ("自己完成", "independent"), ("指导", "supervised"), ("带着我", "supervised"), ("共同", "shared"))]
        position, value = max(mentions, key=lambda item: item[0])
        return value if position >= 0 else None

    @staticmethod
    def _coverage_from_text(text: str) -> str | None:
        return "full" if any(x in text for x in ("完整流程", "整个既定流程", "全部")) else "partial" if any(x in text for x in ("部分", "一部分")) else None

    @staticmethod
    def _confirmed_activity_ids(state: dict[str, Any]) -> set[str]:
        return {r["activity_id"] for r in state.get("task_responsibilities", [])
                if r.get("execution_mode") and r.get("scope", {}).get("coverage")}

    def _ready_to_commit(self, state: dict[str, Any]) -> bool:
        """A confirmed atomic activity is sufficient for an early sample.

        Other activities remain pending and are deliberately excluded from the
        canonical draft sent to the composer.  This is the key difference from
        the old all-slots-required flow.
        """
        return bool(self._confirmed_activity_ids(state))

    def _light_confirmation(self, state: dict[str, Any]) -> dict[str, Any]:
        missing = []
        for r in state.get("task_responsibilities", []):
            if not r.get("execution_mode"): missing.append("这一步是独立、在指导下还是共同完成")
            if not r.get("scope", {}).get("coverage"): missing.append("你完成的是完整流程还是其中一部分")
        return {"kind": "responsibility", "question": "我目前的理解已足够形成经历框架。只差确认：" + "；".join(list(dict.fromkeys(missing))[:1]) + "。", "risk": "responsibility_boundary"}

    def _update_pending_responsibility(self, state: dict[str, Any], text: str) -> None:
        execution = self._execution_from_text(text)
        coverage = "full" if any(x in text for x in ("完整", "全部")) else "partial" if any(x in text for x in ("部分", "一部分")) else None
        for r in state["task_responsibilities"]:
            if execution: r["execution_mode"] = execution
            if coverage: r["scope"]["coverage"] = coverage
        confirmed = self._confirmed_activity_ids(state)
        for activity in state["activities"]:
            activity["status"] = "confirmed" if activity["activity_id"] in confirmed else "needs_user_confirmation"
        state["evidence_records"].append({"evidence_id": f"ev_{len(state['evidence_records'])+1:03d}", "source_text": text, "status": "confirmed"})

    def _commit(self, session_id: str, state: dict[str, Any]) -> bool:
        if not self._ready_to_commit(state): return False
        evidence_ids = [e["evidence_id"] for e in state["evidence_records"]]
        confirmed_ids = self._confirmed_activity_ids(state)
        activities = [deepcopy(a) for a in state["activities"] if a["activity_id"] in confirmed_ids]
        responsibilities = [deepcopy(r) for r in state["task_responsibilities"] if r["activity_id"] in confirmed_ids]
        # The v2 domain gate's canonical spelling is ``user_confirmed``.  The
        # conversation read model uses the shorter ``confirmed`` label only
        # for UI visibility.
        for item in activities:
            item["evidence_ids"] = evidence_ids
            item["status"] = "user_confirmed"
        for item in responsibilities: item["evidence_ids"] = evidence_ids
        overrides = {a["activity_id"]: {k: evidence_ids for k, v in a["components"].items() if v} for a in activities}
        committed_draft = self._draft_for_activities(state["draft"], activities)
        old = (state.get("canonical_experience") or {}).get("experience_id")
        result = self.confirmation_gate.confirm_experience(experience_draft=committed_draft, evidence_records=state["evidence_records"], previous_experience_id=old, user_actions={"canonical_schema_version": "canonical-experience-v2", "activities": activities, "task_responsibilities": responsibilities, "activity_evidence_overrides": overrides})
        if not result.canonical_experience: return False
        if old:
            self.claim_ledger.invalidate_claims_by_experience(session_id, old, "v2_fact_changed")
            for claim in state.get("claims", []):
                if claim.get("experience_id") == old:
                    claim["verification_status"] = "superseded"
                    if claim.get("claim_id") in state["claim_gate_results"]:
                        state["claim_gate_results"][claim["claim_id"]]["status"] = "superseded"
        state["canonical_experience"] = result.canonical_experience
        state["pending_confirmation"] = self._light_confirmation(state) if any(a["activity_id"] not in confirmed_ids for a in state["activities"]) else None
        if state.get("selected_target"):
            self._compose(session_id, state, state["selected_target"])
        return True

    @staticmethod
    def _draft_for_activities(draft: dict[str, Any], activities: list[dict[str, Any]]) -> dict[str, Any]:
        """Pass only confirmed activity components into canonical construction."""
        facts = (draft or {}).get("extracted_facts", {})
        allowed: dict[str, set[str]] = {key: set() for key in ("actions", "methods", "tools", "techniques", "objects", "artifacts")}
        for activity in activities:
            for key, values in activity.get("components", {}).items():
                if key in allowed: allowed[key].update(values)
        # Preserve mandatory neutral context/role fields so the existing gate
        # can validate a canonical record.  The potentially resume-bearing
        # component lists are narrowed to confirmed activities; outcomes stay
        # empty until explicitly confirmed by a later turn.
        committed = {key: deepcopy(facts.get(key, {} if key in {"context", "role", "scope"} else []))
                     for key in ("context", "role", "scope", "collaboration", "techniques", "artifacts")}
        committed["outcomes"] = []
        for key, values in allowed.items():
            committed[key] = [value for value in facts.get(key, []) if value in values]
        return {"extracted_facts": committed, "unknown_items": []}

    def _compose(self, session_id: str, state: dict[str, Any], target: str) -> None:
        state["selected_target"] = target; canonical = state["canonical_experience"]; claims = []
        for claim in self.bullet_composer.compose_bullets(canonical_experience=canonical, role_pack_name=target):
            item = claim.to_dict(); gate = self.claim_gate.validate_claim(bullet_claim=item, canonical_experience=canonical).to_dict(); item["verification_status"] = gate["status"]
            self.claim_ledger.record_claim(session_id=session_id, bullet_claim=item, gate_status=gate["status"]); claims.append(item); state["claim_gate_results"][item["claim_id"]] = gate
        state["claims"] = claims
        state["presentation"] = None

    def _present(self, state: dict[str, Any], preference: str) -> str:
        claims = [claim for claim in state.get("claims", []) if claim.get("verification_status") == "ready"]
        if not claims:
            return "我还缺少能安全写入这句话的责任信息；先补齐当前经历的责任边界。"
        presentation, writer_trace = self.presentation_writer.compose_with_trace(
            claims=claims, canonical=state["canonical_experience"], target=state.get("selected_target"), preference=preference,
        )
        state["_runtime_presentation_trace"] = writer_trace
        state["presentation"] = presentation
        prefix = "按保研方向，我先建议这样写：" if not preference else "可以，我把语气调整得更专业，但不提高你的责任边界："
        return prefix + presentation["wording"]

    def _correct(self, session_id: str, state: dict[str, Any], text: str) -> tuple[str, dict[str, Any] | None]:
        if "独立" in text and any(x in text for x in ("不是", "并非", "其实不")):
            canonical = state.get("canonical_experience") or {}
            if canonical.get("experience_id"):
                self.claim_ledger.invalidate_claims_by_experience(session_id, canonical["experience_id"], "v2_responsibility_corrected")
            for claim in state.get("claims", []):
                claim["verification_status"] = "superseded"
                if claim.get("claim_id") in state["claim_gate_results"]:
                    state["claim_gate_results"][claim["claim_id"]]["status"] = "superseded"
            # This correction is fully specified when it names R and says the
            # work was under guidance.  Update only the R/meta activity; do
            # not erase the independent boundary of literature screening.
            corrected = []
            if "r" in text.lower() and self._execution_from_text(text) == "supervised":
                for activity in state.get("activities", []):
                    components = activity.get("components", {})
                    if "r" in components.get("tools", []) or "meta_analysis" in components.get("methods", []):
                        for responsibility in state.get("task_responsibilities", []):
                            if responsibility.get("activity_id") == activity.get("activity_id"):
                                responsibility["execution_mode"] = "supervised"
                                corrected.append(activity.get("activity_id"))
            if corrected:
                state["evidence_records"].append({"evidence_id": f"ev_{len(state['evidence_records'])+1:03d}", "source_text": text, "status": "confirmed"})
                state["pending_confirmation"] = self._light_confirmation(state) if not self._ready_to_commit(state) else None
                if self._ready_to_commit(state) and self._commit(session_id, state):
                    return "我已将 R 分析改为导师指导下完成，并保留文献检索与筛选的原有责任边界。" + self._sample_message(state, state.get("selected_target")), None
                return "我已将 R 分析改为导师指导下完成；还需要确认缺失的范围后再更新措辞。", state["pending_confirmation"]
            for r in state.get("task_responsibilities", []): r["execution_mode"] = None
            state["pending_confirmation"] = self._light_confirmation(state)
            return "我已撤销“独立完成”的责任表述。请补充这一步实际是在指导下完成还是与他人共同完成。", state["pending_confirmation"]
        return "我已记录这是一条事实纠正；请直接说明更正后的实际做法和责任边界。", None

    def _rewrite(self, session_id: str, state: dict[str, Any], text: str) -> str:
        source = next((c for c in reversed(state["claims"]) if c.get("verification_status") == "ready"), None)
        if not source: return "我还缺少能安全写入这句话的责任信息；先补齐当前经历的责任边界。"
        tone = "High-impact" if "更强" in text or "厉害" in text else "Professional"
        result = self.rewriter.rewrite_claim(source_claim=source, canonical_experience=state["canonical_experience"], tone=tone, instruction=text) if self.rewriter else None
        candidate = result.rewrite_candidate if result else None
        if not isinstance(candidate, dict): return "暂时无法生成受限润色版本；当前已审计要点仍保留在右侧。"
        item = {**source, "claim_id": f"claim_{uuid4().hex[:8]}", "wording": candidate.get("wording", ""), "used_facts": candidate.get("used_facts", []), "dependency_refs": candidate.get("dependency_refs", {}), "evidence_ids": candidate.get("evidence_ids", []), "verification_status": "candidate"}
        gate = self.claim_gate.validate_claim(bullet_claim=item, canonical_experience=state["canonical_experience"]).to_dict()
        if any(item[k] != source[k] for k in ("used_facts", "dependency_refs", "evidence_ids")): gate["status"] = "needs_confirmation"
        item["verification_status"] = gate["status"]; self.claim_ledger.record_claim(session_id=session_id, bullet_claim=item, gate_status=gate["status"]); state["claim_gate_results"][item["claim_id"]] = gate
        if gate["status"] == "ready":
            state["claims"] = [item]; state["rewrite_candidates"].append(item)
            return f"可以，我把语气调整得更专业，但不提高你的责任边界：{item['wording']}"
        return "我先保留原句，因为这版改写可能超出了你已经确认的经历边界。"

    @staticmethod
    def _sample_message(state: dict[str, Any], target: str | None) -> str:
        ready = [claim.get("wording", "") for claim in state.get("claims", []) if claim.get("verification_status") == "ready"]
        if not ready:
            return "我已整理好已确认的部分；只需补齐一项责任信息，就能给你第一版。"
        target_name = {"doctoral_v1": "保研方向", "clinical_research_v1": "临床科研方向", "medical_affairs_v1": "MSL 方向", "health_ai_data_v1": "医疗数据方向"}.get(target or "", "这个方向")
        return f"按{target_name}，我先建议这样写：\n" + "\n".join(f"- {wording}" for wording in ready)

    def _target(self, text: str, plan: dict[str, Any]) -> str | None:
        for action in plan["proposed_actions"]:
            if action.get("type") == "select_target" and action.get("role_pack") in self._PACKS: return action["role_pack"]
        if any(x in text for x in ("保研", "夏令营", "申博", "科研申请")): return "doctoral_v1"
        if any(x in text for x in ("临床科研", "医院科研")): return "clinical_research_v1"
        if any(x in text for x in ("MSL", "医学事务")): return "medical_affairs_v1"
        if any(x in text for x in ("医疗数据", "数字健康")): return "health_ai_data_v1"
        return None

    @staticmethod
    def _is_rewrite(text: str, plan: dict[str, Any]) -> bool:
        return any(a.get("type") == "rewrite_claim" for a in plan["proposed_actions"]) or any(x in text for x in ("专业一点", "更强", "厉害", "弱一点"))

    @staticmethod
    def _is_correction(text: str, state: dict[str, Any]) -> bool:
        return bool(state.get("canonical_experience")) and any(x in text for x in ("其实不是", "并非", "不独立", "不是我独立"))

    def _document(self, session_id: str, state: dict[str, Any]) -> dict[str, Any] | None:
        canonical = state.get("canonical_experience")
        if not canonical: return None
        valid = {x.claim_id for x in self.claim_ledger.get_valid_claims_for_experience(session_id, canonical["experience_id"]) if x.gate_status == "ready"}
        presentation = state.get("presentation") or {}
        if presentation.get("status") == "ready" and set(presentation.get("source_claim_ids", [])).issubset(valid):
            bullets = [{"text": presentation["wording"], "evidence_ids": presentation.get("evidence_ids", [])}]
        else:
            bullets = [{"text": c["wording"], "evidence_ids": c["evidence_ids"]} for c in state.get("claims", []) if c["claim_id"] in valid and c.get("verification_status") == "ready"]
        return {"schema_version": "resume-document-v1", "research_experience": [{"item_id": canonical["experience_id"], "title": "已确认经历", "organization": "待补充", "bullets": bullets}]}

    @staticmethod
    def _audit(state: dict[str, Any]) -> dict[str, int]:
        values = state.get("claims", [])
        return {"ready": sum(x.get("verification_status") == "ready" for x in values), "not_ready": sum(x.get("verification_status") != "ready" for x in values)}
