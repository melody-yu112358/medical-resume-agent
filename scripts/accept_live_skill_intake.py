"""Run one bounded live-model acceptance flow for the resume workspace.

The caller supplies LLM_* environment variables. This script never prints the
API key, retries a model request, or permits more than five model calls.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.adapters.openai_compatible_model_gateway import (
    OpenAICompatibleModelGateway,
)
from medical_career_agent.api import create_app


CALL_LIMIT = 5
EXPECTED_EXPORTS = {
    "evidence-summary.json",
    "export-instructions.txt",
    "resume-data.json",
    "resume-editor.html",
    "resume.html",
    "resume.md",
    "rewrite-comparison.md",
}


@dataclass
class BoundedGateway:
    delegate: OpenAICompatibleModelGateway
    tasks: list[str] = field(default_factory=list)

    def generate(self, *, task: str, context: dict[str, object]) -> str:
        if len(self.tasks) >= CALL_LIMIT:
            raise RuntimeError("live model call limit exceeded")
        self.tasks.append(task)
        return self.delegate.generate(task=task, context=context)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing environment variable: {name}")
    return value


def main() -> int:
    gateway = BoundedGateway(OpenAICompatibleModelGateway(
        base_url=require_env("LLM_BASE_URL"),
        api_key=require_env("LLM_API_KEY"),
        model=require_env("LLM_MODEL"),
        timeout_seconds=float(os.environ.get("LLM_TIMEOUT_SECONDS", "60")),
    ))
    client = create_app(model_gateway=gateway, load_model_from_environment=False).test_client()
    created_response = client.post("/api/conversations", json={})
    if created_response.status_code != 201:
        raise RuntimeError(
            f"conversation creation failed ({created_response.status_code}): "
            f"{created_response.get_data(as_text=True)[:500]}"
        )
    created = created_response.get_json()
    session_id = created["session_id"]

    def message(payload: dict[str, object]) -> dict[str, object]:
        response = client.post(f"/api/conversations/{session_id}/messages", json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"message failed ({response.status_code}): {response.get_json()}")
        return response.get_json()

    profile = {
        "name": "测试同学", "email": "student@example.invalid", "phone": None,
        "location": "上海", "institution": "示例医科大学", "degree": "医学硕士",
        "major": "临床医学", "period": {"start": "2023-09", "end": None, "ongoing": True},
        "awards": "校级科研竞赛一等奖",
        "languages": "CET-6：580",
        "certificates": "GCP 培训证书",
        "research_interests": "心血管循证医学",
    }
    for question_id, value in profile.items():
        message({"action": "answer_candidate_profile", "question_id": question_id,
                 "value": value, "skipped": value is None})
    message({"action": "confirm_candidate_profile"})

    answers = [
        "在导师指导下参与心血管方向的系统综述与 Meta 分析，使用 PubMed、Embase 和 Cochrane 检索文献并完成文献筛选。",
        "我与同学共同完成数据提取，在导师指导下使用 Stata 和 RevMan 进行 Meta 分析与敏感性分析。",
        "我按既定纳入排除标准核对数据提取表，使用 Excel 整理数据，并形成分析图表和论文初稿材料。",
        "我负责数据提取与分析这一明确模块；研究问题和论文定稿由导师决定。我没有主导整个项目，论文尚未投稿。",
    ]
    model_statuses: list[str] = []
    state: dict[str, object] = {}
    for index, text in enumerate(answers):
        card = state.get("question_card") if isinstance(state, dict) else None
        recommended = list((card or {}).get("recommended_option_ids") or [])[:3]
        payload = {
            "action": "submit_experience" if index == 0 else "update_facts",
            "text": text, "display_text": text, "free_text": text,
            "selected_option_ids": recommended, "consent_confirmed": True,
        }
        state = message(payload)["state"]
        model_statuses.append(state["intake_model"]["status"])

    pending = [item for item in state["activity_proposals"]
               if item["status"] == "needs_user_confirmation"]
    confirmed = [{
        "evidence_quote": item["evidence_quote"], "components": item["components"],
        "ownership_level": "contributed", "execution_mode": "supervised",
        "coverage": "partial", "scope_note": "在导师指导下完成已分配步骤",
    } for item in pending]
    state = message({"action": "confirm_activity_proposals", "activity_proposals": confirmed,
                     "proposal_ids": []})["state"]
    state = message({"action": "select_role_packs", "role_packs": ["doctoral_v1"]})["state"]
    state = message({"action": "approve_representative_sample"})["state"]
    state = message({"action": "generate_resume_tiers"})["state"]
    rewrite_ids = {
        item["claim_id"] for item in state["rewrite_candidates"]
    }
    base_claims = [
        item for item in state["generated_claims"]
        if item["claim_id"] not in rewrite_ids
    ]
    candidates_by_source = {
        claim["claim_id"]: [
            item for item in state["rewrite_candidates"]
            if item["source_claim_id"] == claim["claim_id"]
        ]
        for claim in base_claims
    }
    state_before_edit = state
    state = message({"action": "accept_bullets"})["state"]
    state = message({"action": "reopen_audit"})["state"]
    edited_claim = base_claims[0]
    edited_wording = edited_claim["wording"].rstrip("。；") + "；在导师指导下完成。"
    state = message({
        "action": "edit_wording", "claim_id": edited_claim["claim_id"],
        "wording": edited_wording,
    })["state"]
    state = message({"action": "accept_bullets"})["state"]

    exported = client.post(f"/api/conversations/{session_id}/export", json={})
    if exported.status_code != 200:
        raise RuntimeError(f"export failed ({exported.status_code}): {exported.get_json()}")
    files = exported.get_json()["files"]
    markdown = files["resume.md"]
    delivery_data = json.loads(files["resume-data.json"])
    experience_bullets = [
        bullet["text"]
        for section in ("research_experience", "project_experience", "clinical_experience")
        for experience in delivery_data["resume_document"].get(section, [])
        for bullet in experience.get("bullets", [])
        if bullet.get("text")
    ]
    bullets = re.findall(r"^- (.+)$", markdown, flags=re.MULTILINE)
    normalized = [re.sub(r"\s+", "", item) for item in bullets]
    current_rewrite_ids = {
        item["claim_id"] for item in state["rewrite_candidates"]
    }
    responsibility_refs = [
        tuple(item.get("dependency_refs", {}).get("responsibility_ids", []))
        for item in state["generated_claims"]
        if item.get("verification_status") == "ready"
        and item.get("claim_id") not in current_rewrite_ids
    ]
    tier_markdown = [
        delivery_data["tiers"][tier]["markdown"]
        for tier in ("conservative", "professional", "high_impact")
    ]
    checks = {
        "bounded_expected_model_calls": gateway.tasks == (
            ["resume_intake_skill_summary"] * 4
            + ["resume_experience_tier_rewrite"]
        ),
        "all_model_summaries_validated": model_statuses == ["validated"] * 4,
        "profile_confirmed": state["candidate_profile"]["status"] == "confirmed",
        "profile_extras_present": all(item in markdown for item in (
            "校级科研竞赛一等奖", "CET-6：580", "GCP 培训证书", "心血管循证医学",
        )),
        "experience_confirmed": bool(state["confirmed_experiences"]),
        "representative_sample_approved": state["representative_sample"]["status"] == "approved",
        "claims_generated": bool(state["generated_claims"]),
        "deliverable_claims_ready": any(
            item.get("verification_status") == "ready" for item in state["generated_claims"]
        ),
        "complete_export": EXPECTED_EXPORTS.issubset(files),
        "candidate_content_present": "测试同学" in markdown and "示例医科大学" in markdown,
        "no_internal_or_placeholder_text": not re.search(r"ev_\d+|profile_ev_|\[待补\]|请填写", markdown),
        "no_duplicate_bullets": len(normalized) == len(set(normalized)),
        "flagship_has_five_to_nine_distinct_bullets": (
            5 <= len(experience_bullets) <= 9
            and len(experience_bullets) == len(set(experience_bullets))
        ),
        "claims_bind_distinct_responsibilities": (
            bool(responsibility_refs)
            and all(len(refs) == 1 for refs in responsibility_refs)
            and len(responsibility_refs) == len(set(responsibility_refs))
        ),
        "three_complete_tiers": all(
            "# 测试同学" in value
            and "## 教育背景" in value
            and "## 科研经历" in value
            and len(re.findall(r"^- ", value, flags=re.MULTILINE)) >= len(experience_bullets)
            for value in tier_markdown
        ),
        "all_tier_candidates_ready": bool(candidates_by_source) and all(
            {item["tone"] for item in candidates} == {
                "Conservative", "Professional", "High-impact",
            }
            and all(item["selected"] and item["gate"]["status"] == "ready"
                    for item in candidates)
            for candidates in candidates_by_source.values()
        ),
        "three_distinct_tier_wordings_per_claim": all(
            len({
                next(item for item in state_before_edit["generated_claims"]
                     if item["claim_id"] == candidate["claim_id"])["wording"]
                for candidate in candidates
            }) == 3
            for candidates in candidates_by_source.values()
        ),
        "user_edit_reaudited": (
            state["stage"] == "delivery"
            and delivery_data["edit_status"] == "user-edited"
        ),
        "responsibility_boundary_preserved": not any(
            re.search(r"主导|独立完成|负责全部|论文已发表", value)
            for value in tier_markdown
        ),
    }
    report = {
        "status": "passed" if all(checks.values()) else "failed",
        "model_calls": len(gateway.tasks), "model_tasks": gateway.tasks,
        "model_summary_statuses": model_statuses, "checks": checks,
        "counts": {"experiences": len(state["confirmed_experiences"]),
                   "claims": len(state["generated_claims"]), "bullets": len(bullets),
                   "experience_bullets": len(experience_bullets)},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    client.delete(f"/api/conversations/{session_id}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
