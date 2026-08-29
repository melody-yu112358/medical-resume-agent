"""Opt-in prompt ablation for activity proposals; this does not modify product prompts."""
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
from medical_career_agent.adapters.openai_compatible_model_gateway import ModelGatewayError, OpenAICompatibleModelGateway
from medical_career_agent.services.bullet_composer import BulletComposerService
from medical_career_agent.services.claim_gate import ClaimGateService
from medical_career_agent.services.claim_ledger import ClaimLedgerService
from medical_career_agent.services.confirmation_gate import ConfirmationGateService
from medical_career_agent.services.experience_draft import ExperienceDraftService
from medical_career_agent.services.resume_conversation_agent import ResumeConversationAgent


REQUIRED_ENVIRONMENT = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")
BASE_PROMPT = "Return JSON only. Propose atomic activities, never facts outside vocabulary. Each proposal needs evidence_quote copied verbatim from user_text, components, ownership_level, execution_mode, and coverage. Split different actions or responsibility boundaries into separate activities. Use unknown for any ownership, execution, or coverage dimension not explicitly supported by the quote; never infer supervised from a mentor defining a plan, or partial from collaboration alone. Do not return canonical data or state patches."
VARIANTS = {
    "A_base": BASE_PROMPT,
    "B_exaggeration": BASE_PROMPT + " Keep factual user actions even when the user requests exaggeration; do not turn requested leadership, publication quality, or unsupported outcomes into facts.",
    "C_retrieval": BASE_PROMPT + " Literature retrieval/search must include actions:retrieve_literature; tools or methods alone are not activities.",
    "D_few_shot": BASE_PROMPT + " Examples: input 'I searched literature with PubMed' -> one activity with actions:['retrieve_literature'] and tools:['pubmed']. Input 'I screened only part of the literature but want to claim project leadership' -> one activity with actions:['screen_studies'], coverage:'partial'; do not claim leadership.",
    "E_current": "Return JSON only. Propose atomic activities, never facts outside vocabulary. Each proposal needs evidence_quote copied verbatim from user_text, components, ownership_level, execution_mode, and coverage. Split different actions or responsibility boundaries. Use unknown for any ownership, execution, or coverage dimension not explicitly supported by the quote; never infer supervised from a mentor defining a plan, or partial from collaboration alone. Keep factual user actions even if the user requests exaggeration or mentions an uncertain outcome; do not make outcome-only or another-person-decision activities. Literature retrieval/search must include actions:retrieve_literature; screening uses actions:screen_studies; tools or methods alone are not activities. Split guideline review from case-presentation preparation, and exclude a presentation completed by another person. “只” and “共同” do not mean partial. Do not return canonical data or state patches.",
}


def _configured_gateway() -> OpenAICompatibleModelGateway | None:
    values = {name: os.environ.get(name, "").strip() for name in REQUIRED_ENVIRONMENT}
    if not all(values.values()):
        print("SKIPPED: configure " + ", ".join(name for name, value in values.items() if not value))
        return None
    return OpenAICompatibleModelGateway(base_url=values["LLM_BASE_URL"], api_key=values["LLM_API_KEY"], model=values["LLM_MODEL"])


def _validator(workspace: Path) -> ResumeConversationAgent:
    return ResumeConversationAgent(
        sessions=FileSessionStore(workspace / "sessions"), experience_drafter=ExperienceDraftService(),
        confirmation_gate=ConfirmationGateService(), bullet_composer=BulletComposerService(),
        claim_gate=ClaimGateService(), claim_ledger=ClaimLedgerService(workspace / "sessions"),
    )


def _context(prompt: str, text: str, facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "instruction": prompt, "user_text": text,
        "allowed_components": {key: facts.get(key, []) for key in ("actions", "methods", "tools", "techniques", "objects", "artifacts")},
        "ownership_levels": ["unknown", "contributed", "owned_component", "led_delivery", "accountable"],
        "execution_modes": ["unknown", "supervised", "independent", "shared"],
        "coverage": ["unknown", "full", "partial"],
        "response_shape": {"activity_proposals": [{"evidence_quote": "verbatim substring", "components": {"actions": [], "methods": [], "tools": [], "techniques": [], "objects": [], "artifacts": []}, "ownership_level": "unknown", "execution_mode": "unknown", "coverage": "unknown", "scope_note": None}]},
    }


def _structured_raw(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"parse_status": "json_not_object", "activity_proposals": None}
    proposals = value.get("activity_proposals")
    if not isinstance(proposals, list):
        return {"parse_status": "activity_proposals_not_array", "activity_proposals": None}
    return {"parse_status": "ok", "activity_proposals": proposals}


def _run_once(gateway: OpenAICompatibleModelGateway, validator: ResumeConversationAgent, case: dict[str, Any], variant: str) -> dict[str, Any]:
    text = case["user_input"]
    facts = ExperienceDraftService().draft(experience_text=text, consent_confirmed=True).extracted_facts
    try:
        raw_text = gateway.generate(task="resume_activity_proposals", context=_context(VARIANTS[variant], text, facts))
    except ModelGatewayError as exc:
        return {"model_status": "model_error", "error": str(exc)}
    try:
        raw_value = json.loads(raw_text)
    except json.JSONDecodeError:
        return {"model_status": "json_invalid", "structured_raw": None}
    structured = _structured_raw(raw_value)
    raw_proposals = structured["activity_proposals"] or []
    accepted, audit = validator._validate_activity_proposals_with_audit(raw_proposals, text, facts)
    warnings = [warning for proposal in accepted for warning in proposal["semantic_warnings"]]
    inflation = [warning for warning in warnings if "execution_mode" in warning or "strong ownership" in warning]
    return {
        "model_status": "empty" if structured["parse_status"] == "ok" and not raw_proposals else structured["parse_status"],
        "structured_raw": structured,
        "raw_proposal_count": len(raw_proposals), "accepted_proposal_count": len(accepted),
        "accepted_proposals": accepted, "hard_rejections": audit["hard_rejections"],
        "action_missing": any(not (item.get("components") or {}).get("actions") for item in raw_proposals if isinstance(item, dict)),
        "unknown_fields": [
            {"ownership_level": item.get("ownership_level"), "execution_mode": item.get("execution_mode"), "coverage": item.get("coverage")}
            for item in raw_proposals if isinstance(item, dict)
        ],
        "quote_not_substring": [item.get("evidence_quote") for item in raw_proposals if isinstance(item, dict) and item.get("evidence_quote") not in text],
        "responsibility_inflation_warnings": inflation,
    }


def _summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "runs": len(runs), "model_empty": sum(run.get("model_status") == "empty" for run in runs),
        "json_invalid": sum(run.get("model_status") == "json_invalid" for run in runs),
        "schema_failed": sum(run.get("model_status") in {"json_not_object", "activity_proposals_not_array"} for run in runs),
        "any_raw_proposal": sum(run.get("raw_proposal_count", 0) > 0 for run in runs),
        "any_accepted_proposal": sum(run.get("accepted_proposal_count", 0) > 0 for run in runs),
        "hard_rejections": sum(len(run.get("hard_rejections", [])) for run in runs),
        "action_missing": sum(bool(run.get("action_missing")) for run in runs),
        "quote_not_substring": sum(len(run.get("quote_not_substring", [])) for run in runs),
        "responsibility_inflation_warnings": sum(len(run.get("responsibility_inflation_warnings", [])) for run in runs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "data" / "evaluations" / "activity_proposal_prompt_ablation_cases.json")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repetitions < 3:
        raise ValueError("--repetitions must be at least 3")
    gateway = _configured_gateway()
    if gateway is None:
        return 0
    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    output = args.output or ROOT / "tmp" / "model-evals" / f"activity-proposal-prompt-ablation-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="medical-resume-prompt-ablation-") as temporary:
        validator = _validator(Path(temporary))
        results = {}
        for variant in VARIANTS:
            variant_runs = {case["id"]: [_run_once(gateway, validator, case, variant) for _ in range(args.repetitions)] for case in cases}
            results[variant] = {"runs": variant_runs, "summary": _summary([run for runs in variant_runs.values() for run in runs])}
    report = {"schema_version": "activity-proposal-prompt-ablation-v1", "generated_at": datetime.now(timezone.utc).isoformat(), "case_count": len(cases), "repetitions": args.repetitions, "variants": list(VARIANTS), "results": results}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote activity proposal prompt ablation report to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
