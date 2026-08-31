from __future__ import annotations

import json

from medical_career_agent.api import create_app


SOURCE = "我独立完成系统综述的文献筛选。"
PROPOSAL = {
    "evidence_quote": SOURCE,
    "components": {
        "actions": ["screen_studies"], "methods": ["systematic_review"],
        "tools": [], "techniques": [], "objects": ["medical_literature"],
        "artifacts": [],
    },
    "ownership_level": "owned_component", "execution_mode": "independent",
    "coverage": "full", "scope_note": None,
}
SAFE_WORDING = {
    "Conservative": "在确认范围内独立完成系统综述文献筛选。",
    "Professional": "独立完成系统综述文献筛选流程。",
    "High-impact": "围绕系统综述流程，独立推进文献筛选工作。",
}


class TierGateway:
    def __init__(self, *, unsafe_high_impact=False):
        self.calls = []
        self.unsafe_high_impact = unsafe_high_impact

    def generate(self, *, task, context):
        assert task == "resume_constrained_rewrite"
        self.calls.append(context)
        source = context["source_claim"]
        wording = SAFE_WORDING[context["tone"]]
        if self.unsafe_high_impact and context["tone"] == "High-impact":
            wording = "主导项目并负责全部系统综述流程。"
        return json.dumps({
            "wording": wording, "used_facts": source["used_facts"],
            "dependency_refs": source["dependency_refs"],
            "evidence_ids": source["evidence_ids"],
        }, ensure_ascii=False)


class BatchedTierGateway:
    def __init__(self, *, omit_high_impact=False, unsafe_high_impact=False):
        self.calls = []
        self.omit_high_impact = omit_high_impact
        self.unsafe_high_impact = unsafe_high_impact

    def generate(self, *, task, context):
        assert task == "resume_experience_tier_rewrite"
        self.calls.append(context)
        candidates = []
        for source in context["source_claims"]:
            for tone in ("Conservative", "Professional", "High-impact"):
                if self.omit_high_impact and tone == "High-impact":
                    continue
                wording = SAFE_WORDING[tone]
                if self.unsafe_high_impact and tone == "High-impact":
                    wording = "主导项目并负责全部系统综述流程。"
                candidates.append({
                    "source_claim_id": source["claim_id"], "tone": tone,
                    "wording": wording, "used_facts": source["used_facts"],
                    "dependency_refs": source["dependency_refs"],
                    "evidence_ids": source["evidence_ids"],
                })
        return json.dumps({"rewrite_candidates": candidates}, ensure_ascii=False)


def _message(client, session_id, payload):
    response = client.post(f"/api/conversations/{session_id}/messages", json=payload)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _composed_conversation(gateway=None):
    client = create_app(model_gateway=gateway, load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    _message(client, session_id, {"text": SOURCE, "consent_confirmed": True})
    _message(client, session_id, {
        "action": "confirm_activity_proposals", "activity_proposals": [PROPOSAL],
        "proposal_ids": [],
    })
    sample = _message(client, session_id, {
        "action": "select_role_packs", "role_packs": ["doctoral_v1"],
    })
    assert sample["stage"] == "representative_sample"
    composed = _message(client, session_id, {"action": "approve_representative_sample"})
    return client, session_id, composed


def _candidate_for(state, source_id, tone):
    meta = next(
        item for item in state["rewrite_candidates"]
        if item["source_claim_id"] == source_id and item["tone"] == tone
    )
    claim = next(item for item in state["generated_claims"] if item["claim_id"] == meta["claim_id"])
    return meta, claim


def test_three_complete_tiers_preserve_independent_selections_and_single_call_actions():
    gateway = TierGateway()
    client, session_id, composed = _composed_conversation(gateway)
    source = composed["state"]["generated_claims"][0]
    base_wording = composed["resume_document"]["research_experience"][0]["bullets"][0]["text"]
    assert composed["state"]["selected_resume_tier"] == "professional"

    conservative = _message(client, session_id, {
        "action": "rewrite_claim", "source_claim_id": source["claim_id"],
        "tone": "Conservative", "instruction": "更稳妥",
    })
    assert len(gateway.calls) == 1
    assert conservative["resume_document"]["research_experience"][0]["bullets"][0]["text"] == base_wording
    conservative_meta, conservative_claim = _candidate_for(conservative["state"], source["claim_id"], "Conservative")
    assert conservative_meta["selected"] is False
    nested = _message(client, session_id, {
        "action": "rewrite_claim", "source_claim_id": conservative_claim["claim_id"],
        "tone": "Professional", "instruction": "再改一次",
    })
    assert len(gateway.calls) == 1
    assert "避免对候选改写再次改写" in nested["assistant_message"]

    selected_conservative = _message(client, session_id, {
        "action": "select_rewrite_candidate", "claim_id": conservative_claim["claim_id"],
    })
    assert len(gateway.calls) == 1
    assert selected_conservative["state"]["selected_resume_tier"] == "conservative"
    assert selected_conservative["resume_document"]["research_experience"][0]["bullets"][0]["text"] == SAFE_WORDING["Conservative"]

    professional = _message(client, session_id, {
        "action": "rewrite_claim", "source_claim_id": source["claim_id"],
        "tone": "Professional", "instruction": "更专业",
    })
    assert len(gateway.calls) == 2
    professional_meta, professional_claim = _candidate_for(professional["state"], source["claim_id"], "Professional")
    selected_professional = _message(client, session_id, {
        "action": "select_rewrite_candidate", "claim_id": professional_claim["claim_id"],
    })
    assert len(gateway.calls) == 2
    selected_by_tone = {
        item["tone"]: item["selected"] for item in selected_professional["state"]["rewrite_candidates"]
    }
    assert selected_by_tone == {"Conservative": True, "Professional": True}
    assert selected_professional["state"]["selected_resume_tier"] == "professional"
    assert selected_professional["resume_document"]["research_experience"][0]["bullets"][0]["text"] == SAFE_WORDING["Professional"]

    switched = _message(client, session_id, {"action": "select_resume_tier", "tier": "conservative"})
    assert len(gateway.calls) == 2
    assert switched["resume_document"]["research_experience"][0]["bullets"][0]["text"] == SAFE_WORDING["Conservative"]
    _message(client, session_id, {"action": "select_resume_tier", "tier": "professional"})
    _message(client, session_id, {"action": "accept_bullets"})

    bundle = client.post(
        f"/api/conversations/{session_id}/export",
        json={"basics": {"name": "测试同学", "contact": "test@example.invalid"}},
    ).get_json()["files"]
    data = json.loads(bundle["resume-data.json"])
    assert data["schema_version"] == "medical-resume-data-v1"
    assert data["selected_tier"] == "professional"
    assert set(data["tiers"]) == {"conservative", "professional", "high_impact"}
    assert SAFE_WORDING["Conservative"] in data["tiers"]["conservative"]["markdown"]
    assert SAFE_WORDING["Professional"] in data["tiers"]["professional"]["markdown"]
    assert base_wording in data["tiers"]["high_impact"]["markdown"]
    for tier in data["tiers"].values():
        markdown = tier["markdown"]
        assert "# 测试同学" in markdown
        assert "## 科研经历" in markdown
        assert "evidence_id" not in markdown
        assert "doctoral_v1" not in markdown
    assert bundle["resume.md"] == data["tiers"]["professional"]["markdown"]
    assert SAFE_WORDING["Professional"] in bundle["resume.html"]
    assert SAFE_WORDING["Professional"] in bundle["resume-editor.html"]
    assert data["candidate"]["target_direction"] == "学术升学与科研申请"
    assert data["fact_card"]["evidence_bound"] is True
    assert data["audit"]["status"] == "ready"


def test_rejected_high_impact_candidate_never_enters_tier_or_export():
    gateway = TierGateway(unsafe_high_impact=True)
    client, session_id, composed = _composed_conversation(gateway)
    source = composed["state"]["generated_claims"][0]
    base_wording = composed["resume_document"]["research_experience"][0]["bullets"][0]["text"]

    rewritten = _message(client, session_id, {
        "action": "rewrite_claim", "source_claim_id": source["claim_id"],
        "tone": "High-impact", "instruction": "更强",
    })
    meta, candidate = _candidate_for(rewritten["state"], source["claim_id"], "High-impact")
    assert len(gateway.calls) == 1
    assert meta["gate"]["status"] != "ready"
    refused = _message(client, session_id, {
        "action": "select_rewrite_candidate", "claim_id": candidate["claim_id"],
    })
    assert refused["state"]["selected_resume_tier"] == "professional"
    switched = _message(client, session_id, {"action": "select_resume_tier", "tier": "high_impact"})
    assert switched["resume_document"]["research_experience"][0]["bullets"][0]["text"] == base_wording
    _message(client, session_id, {"action": "accept_bullets"})
    data = json.loads(client.post(
        f"/api/conversations/{session_id}/export", json={"basics": {"name": "测试同学"}},
    ).get_json()["files"]["resume-data.json"])
    assert "主导项目" not in data["tiers"]["high_impact"]["markdown"]
    assert base_wording in data["tiers"]["high_impact"]["markdown"]


def test_one_batched_call_generates_and_selects_all_three_audited_tiers():
    gateway = BatchedTierGateway()
    client, session_id, composed = _composed_conversation(gateway)
    source = composed["state"]["generated_claims"][0]

    generated = _message(client, session_id, {"action": "generate_resume_tiers"})

    assert len(gateway.calls) == 1
    assert len(gateway.calls[0]["source_claims"]) == 1
    assert {
        item["tone"] for item in generated["state"]["rewrite_candidates"]
    } == {"Conservative", "Professional", "High-impact"}
    assert all(item["selected"] for item in generated["state"]["rewrite_candidates"])
    assert all(
        item["source_claim_id"] == source["claim_id"]
        for item in generated["state"]["rewrite_candidates"]
    )
    for tier, wording in (
        ("conservative", SAFE_WORDING["Conservative"]),
        ("professional", SAFE_WORDING["Professional"]),
        ("high_impact", SAFE_WORDING["High-impact"]),
    ):
        switched = _message(
            client, session_id, {"action": "select_resume_tier", "tier": tier},
        )
        assert switched["resume_document"]["research_experience"][0]["bullets"][0]["text"] == wording


def test_incomplete_batched_response_is_atomic_and_keeps_existing_candidates():
    gateway = BatchedTierGateway(omit_high_impact=True)
    client, session_id, composed = _composed_conversation(gateway)
    before_claim_ids = {
        item["claim_id"] for item in composed["state"]["generated_claims"]
    }

    rejected = _message(client, session_id, {"action": "generate_resume_tiers"})

    assert len(gateway.calls) == 1
    assert {item["claim_id"] for item in rejected["state"]["generated_claims"]} == before_claim_ids
    assert rejected["state"]["rewrite_candidates"] == []
    assert "已保留原审计要点" in rejected["assistant_message"]


def test_batched_unsafe_candidate_falls_back_without_blocking_safe_tiers():
    gateway = BatchedTierGateway(unsafe_high_impact=True)
    client, session_id, composed = _composed_conversation(gateway)
    base_wording = composed["resume_document"]["research_experience"][0]["bullets"][0]["text"]

    generated = _message(client, session_id, {"action": "generate_resume_tiers"})

    candidates = {item["tone"]: item for item in generated["state"]["rewrite_candidates"]}
    assert candidates["Conservative"]["selected"] is True
    assert candidates["Professional"]["selected"] is True
    assert candidates["High-impact"]["selected"] is False
    switched = _message(
        client, session_id, {"action": "select_resume_tier", "tier": "high_impact"},
    )
    assert switched["resume_document"]["research_experience"][0]["bullets"][0]["text"] == base_wording
    assert "主导项目" not in switched["resume_document"]["research_experience"][0]["bullets"][0]["text"]


def test_no_model_still_exports_three_complete_professional_default_tiers():
    client, session_id, composed = _composed_conversation()
    assert composed["state"]["selected_resume_tier"] == "professional"
    invalid = _message(client, session_id, {"action": "select_resume_tier", "tier": "invented"})
    assert invalid["state"]["selected_resume_tier"] == "professional"
    _message(client, session_id, {"action": "accept_bullets"})
    data = json.loads(client.post(
        f"/api/conversations/{session_id}/export", json={"basics": {"name": "测试同学"}},
    ).get_json()["files"]["resume-data.json"])
    markdowns = [data["tiers"][tier]["markdown"] for tier in ("conservative", "professional", "high_impact")]
    assert data["selected_tier"] == "professional"
    assert markdowns[0] == markdowns[1] == markdowns[2]
    assert "## 科研经历" in markdowns[0]
