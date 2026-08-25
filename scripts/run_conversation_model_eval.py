"""Run synthetic, opt-in evaluations against the configured conversation model.

This is intentionally a script rather than a default pytest test: each run may
make real provider requests.  It persists only normalized, synthetic evaluation
artifacts and never provider credentials or raw model responses.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.adapters.file_session_store import FileSessionStore
from medical_career_agent.adapters.openai_compatible_model_gateway import (
    ModelGatewayError,
    OpenAICompatibleModelGateway,
)
from medical_career_agent.services.bullet_composer import BulletComposerService
from medical_career_agent.services.claim_gate import ClaimGateService
from medical_career_agent.services.claim_ledger import ClaimLedgerService
from medical_career_agent.services.confirmation_gate import ConfirmationGateService
from medical_career_agent.services.conversation_model_gateway import (
    ModelGatewayConversationGateway,
)
from medical_career_agent.services.experience_draft import ExperienceDraftService
from medical_career_agent.services.resume_conversation_agent import ResumeConversationAgent


REQUIRED_ENVIRONMENT = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")
TONES = ("Conservative", "Professional", "High-impact")


def _configured_gateway() -> OpenAICompatibleModelGateway | None:
    values = {name: os.environ.get(name, "").strip() for name in REQUIRED_ENVIRONMENT}
    if not all(values.values()):
        missing = ", ".join(name for name, value in values.items() if not value)
        print(f"SKIPPED: configure {missing} to run real-model evaluation.")
        return None
    return OpenAICompatibleModelGateway(
        base_url=values["LLM_BASE_URL"], api_key=values["LLM_API_KEY"], model=values["LLM_MODEL"],
    )


def _new_agent(workspace: Path, gateway: OpenAICompatibleModelGateway) -> ResumeConversationAgent:
    return ResumeConversationAgent(
        sessions=FileSessionStore(workspace / "sessions"),
        experience_drafter=ExperienceDraftService(),
        confirmation_gate=ConfirmationGateService(),
        bullet_composer=BulletComposerService(),
        claim_gate=ClaimGateService(),
        claim_ledger=ClaimLedgerService(workspace / "sessions"),
        language_gateway=ModelGatewayConversationGateway(gateway),
    )


def _proposal_view(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "proposal_id": proposal.get("proposal_id"),
        "activity_id": proposal.get("activity_id"),
        "evidence_quote": proposal.get("evidence_quote"),
        "components": proposal.get("components", {}),
        "semantic_warnings": proposal.get("semantic_warnings", []),
        "candidate_responsibility": {
            "responsibility_id": proposal.get("responsibility_id"),
            "ownership_level": proposal.get("ownership_level"),
            "execution_mode": proposal.get("execution_mode"),
            "scope": proposal.get("scope", {}),
        },
        "status": proposal.get("status"),
    }


def _risk_summary(gates: list[dict[str, Any]], proposal_count: int) -> dict[str, bool]:
    failed = [item for gate in gates for item in gate.get("failed_checks", [])]
    lower = " ".join(failed).lower()
    return {
        "unsupported_or_invalid": proposal_count == 0 or any(gate.get("status") != "ready" for gate in gates),
        "responsibility_inflation": any(
            marker in lower for marker in ("responsibility", "ownership", "scope", "project_role")
        ),
    }


def _not_run_rewrites(reason: str) -> dict[str, dict[str, Any]]:
    return {tone: {"status": "not_run", "reason": reason} for tone in TONES}


def _latest_model_intent(state: dict[str, Any]) -> dict[str, Any] | None:
    entries = state.get("language_audit", [])
    return entries[-1] if entries else None


def _latest_proposal_audit(state: dict[str, Any]) -> dict[str, Any] | None:
    entries = state.get("proposal_audits", [])
    return entries[-1] if entries else None


def evaluate_case(case: dict[str, Any], gateway: OpenAICompatibleModelGateway, workspace: Path) -> dict[str, Any]:
    agent = _new_agent(workspace, gateway)
    session_id = f"eval_{case['id']}"
    agent.create(session_id)
    base = {"case_id": case["id"], "tags": case.get("tags", []), "user_input": case["user_input"]}
    try:
        intake = agent.handle_message(session_id, {"text": case["user_input"], "consent_confirmed": True})
        state = agent.read(session_id)["state"]
    except (ModelGatewayError, OSError, ValueError) as exc:
        return {**base, "status": "model_error", "error": str(exc), "rewrites": _not_run_rewrites("activity proposal call failed")}

    proposals = [item for item in state.get("activity_proposals", []) if item.get("status") == "needs_user_confirmation"]
    result: dict[str, Any] = {
        **base,
        "status": "proposal_complete",
        "assistant_message": intake.get("assistant_message"),
        "pending_question": intake.get("pending_question"),
        "stage": state.get("stage"),
        "model_intent": _latest_model_intent(state),
        "proposal_validation": _latest_proposal_audit(state),
        "activity_proposals": [_proposal_view(item) for item in proposals],
        "proposal_count": len(proposals),
        "rewrites": _not_run_rewrites("no user-confirmable model activity proposal"),
        "claim_gate": [],
    }
    confirmable = [
        item for item in proposals
        if item.get("ownership_level") != "unknown"
        and item.get("execution_mode") != "unknown"
        and (item.get("scope") or {}).get("coverage") != "unknown"
        and not item.get("semantic_warnings")
    ]
    if not confirmable:
        result["simulated_confirmation"] = {
            "status": "not_run",
            "reason": "unknown responsibility field or semantic warning requires a real user decision",
        }
        result["risk_summary"] = _risk_summary([], len(proposals))
        return result

    # This is the explicit simulated user-confirmation boundary for the eval.
    # Raw model proposals are never placed in canonical state before this call.
    try:
        agent.handle_message(session_id, {"action": "confirm_activity_proposals", "proposal_ids": [item["proposal_id"] for item in confirmable]})
        agent.handle_message(session_id, {"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
        state = agent.read(session_id)["state"]
    except (ModelGatewayError, OSError, ValueError) as exc:
        result.update({"status": "confirmation_error", "error": str(exc), "risk_summary": _risk_summary([], len(proposals))})
        return result
    result["simulated_confirmation"] = {"status": "confirmed", "proposal_ids": [item["proposal_id"] for item in confirmable]}

    source = next((item for item in state.get("generated_claims", []) if item.get("verification_status") == "ready"), None)
    if not source:
        result["status"] = "no_ready_source_claim"
        result["claim_gate"] = list(state.get("claim_gate_results", {}).values())
        result["risk_summary"] = _risk_summary(result["claim_gate"], len(proposals))
        return result

    rewrites: dict[str, dict[str, Any]] = {}
    for tone in TONES:
        try:
            agent.handle_message(session_id, {
                "action": "rewrite_claim", "source_claim_id": source["claim_id"],
                "tone": tone, "instruction": case.get("rewrite_instruction", "专业一点，但不要超过责任边界"),
            })
            state = agent.read(session_id)["state"]
            candidate = state["generated_claims"][-1]
            gate = state["claim_gate_results"].get(candidate["claim_id"], {})
            rewrites[tone] = {
                "status": candidate.get("verification_status"), "wording": candidate.get("wording"),
                "used_facts": candidate.get("used_facts", []), "dependency_refs": candidate.get("dependency_refs", {}),
                "evidence_ids": candidate.get("evidence_ids", []), "claim_gate": gate,
            }
        except (ModelGatewayError, OSError, ValueError) as exc:
            rewrites[tone] = {"status": "model_error", "error": str(exc)}
    result["status"] = "rewrite_complete"
    result["source_claim"] = {
        "claim_id": source["claim_id"], "wording": source["wording"],
        "used_facts": source["used_facts"], "dependency_refs": source["dependency_refs"],
        "evidence_ids": source["evidence_ids"],
    }
    result["rewrites"] = rewrites
    result["claim_gate"] = [item.get("claim_gate", {}) for item in rewrites.values()]
    result["risk_summary"] = _risk_summary(result["claim_gate"], len(proposals))
    return result


def _metrics(results: list[dict[str, Any]]) -> dict[str, int]:
    rewrites = [rewrite for item in results for rewrite in item.get("rewrites", {}).values()]
    return {
        "proposal_zero": sum(item.get("proposal_count") == 0 for item in results),
        "proposal_nonzero": sum(item.get("proposal_count", 0) > 0 for item in results),
        "hard_rejections": sum(len((item.get("proposal_validation") or {}).get("hard_rejections", [])) for item in results),
        "semantic_warnings": sum(len(proposal.get("semantic_warnings", [])) for item in results for proposal in item.get("activity_proposals", [])),
        "rewrite_complete": sum(item.get("status") == "rewrite_complete" for item in results),
        "rewrite_ready": sum(rewrite.get("status") == "ready" for rewrite in rewrites),
        "rewrite_traceability_rejected": sum(any("rewrite_source_traceability" in check for check in rewrite.get("claim_gate", {}).get("failed_checks", [])) for rewrite in rewrites),
        "identical_three_tones": sum(
            item.get("rewrites", {}).get("Conservative", {}).get("status") == "ready"
            and item["rewrites"]["Conservative"].get("wording") == item["rewrites"].get("Professional", {}).get("wording")
            and item["rewrites"].get("Professional", {}).get("wording") == item["rewrites"].get("High-impact", {}).get("wording")
            for item in results
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "data" / "evaluations" / "conversation_model_eval_cases.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, help="Run only the first N synthetic cases.")
    args = parser.parse_args()
    gateway = _configured_gateway()
    if gateway is None:
        return 0
    cases = json.loads(args.cases.read_text(encoding="utf-8")).get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("evaluation cases must contain a cases array")
    cases = cases[:args.limit] if args.limit is not None else cases
    output = args.output or ROOT / "tmp" / "model-evals" / f"conversation-model-eval-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="medical-resume-model-eval-") as temporary:
        results = [evaluate_case(case, gateway, Path(temporary) / case["id"]) for case in cases]
    report = {
        "schema_version": "conversation-model-eval-report-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(results),
        "metrics": _metrics(results),
        "cases": results,
        "human_scoring_template": ["fact_fidelity", "responsibility_fidelity", "activity_decomposition_quality", "conversation_naturalness", "rewrite_quality", "overclaim_risk"],
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} synthetic model-eval records to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
