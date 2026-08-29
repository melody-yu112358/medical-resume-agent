import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.api import create_app


class Gateway:
    def __init__(self): self.calls = []

    def generate(self, *, task, context):
        self.calls.append(task)
        if task == "chat_first_resume_v2_turn":
            if "完整的一句话" in context["user_text"]:
                return json.dumps({"assistant_message": "我会把已确认内容合成一句。", "proposed_actions": [{"type": "compose_sample"}], "confirmation": None, "needs_user_reply": False}, ensure_ascii=False)
            if "什么意思" in context["user_text"]:
                return json.dumps({"assistant_message": "我会把已确认的真实经历整理成适合简历的表达，不会增加你没有做过的内容。", "proposed_actions": [], "confirmation": None, "needs_user_reply": False}, ensure_ascii=False)
            return json.dumps({"assistant_message": "我会基于你提供的原文整理经历。", "proposed_actions": [{"type": "propose_fact", "evidence_quote": context["user_text"]}], "confirmation": None, "needs_user_reply": False}, ensure_ascii=False)
        if task == "resume_constrained_rewrite":
            source = context["source_claim"]
            return json.dumps({"wording": source["wording"], "used_facts": source["used_facts"], "dependency_refs": source["dependency_refs"], "evidence_ids": source["evidence_ids"]}, ensure_ascii=False)
        return json.dumps({})


def make_client():
    gateway = Gateway()
    return create_app(model_gateway=gateway, load_model_from_environment=False).test_client(), gateway


def post(client, sid, payload):
    response = client.post(f"/api/conversations-v2/{sid}/messages", json=payload)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def start(client):
    response = client.post("/api/conversations-v2", json={})
    assert response.status_code == 201
    return response.get_json()["session_id"]


def test_golden_path_a_first_sample_target_and_tiered_rewrite():
    client, gateway = make_client(); sid = start(client)
    first = post(client, sid, {"text": "我在导师指导下负责用 R 完成 meta 分析整个既定流程。", "consent_confirmed": True})
    assert first["state"]["canonical_experience"]
    composed = post(client, sid, {"text": "保研"})
    assert composed["audit_status"]["ready"] == 1
    assert "按保研方向，我先建议这样写：" in composed["assistant_message"]
    rewritten = post(client, sid, {"text": "专业一点，但不要显得我主导"})
    assert rewritten["audit_status"]["ready"] == 1
    assert "可以，我把语气调整得更专业" in rewritten["assistant_message"]
    assert rewritten["resume_document"]["research_experience"][0]["bullets"]
    assert "chat_first_resume_v2_turn" in gateway.calls
    assert "resume_presentation_writer" in gateway.calls


def test_golden_path_b_correction_invalidates_then_recomputes_affected_claim():
    client, _ = make_client(); sid = start(client)
    post(client, sid, {"text": "我独立负责用 R 完成 meta 分析整个既定流程。", "consent_confirmed": True})
    before = post(client, sid, {"text": "保研"})
    assert before["audit_status"]["ready"] == 1
    corrected = post(client, sid, {"text": "R其实不是我独立做的。"})
    assert corrected["confirmation"]["risk"] == "responsibility_boundary"
    assert not corrected["resume_document"]["research_experience"][0]["bullets"]
    after = post(client, sid, {"text": "R 分析是在导师指导下完成完整流程。", "consent_confirmed": True})
    assert after["audit_status"]["ready"] == 1
    assert "在指导下" in after["resume_document"]["research_experience"][0]["bullets"][0]["text"]


def test_golden_path_c_rewrite_updates_live_document_without_overclaim():
    client, _ = make_client(); sid = start(client)
    post(client, sid, {"text": "我在导师指导下负责用 R 完成 meta 分析整个既定流程。", "consent_confirmed": True})
    post(client, sid, {"text": "保研"})
    result = post(client, sid, {"text": "专业一点，但不要显得我主导"})
    bullet = result["resume_document"]["research_experience"][0]["bullets"][0]["text"]
    assert bullet == result["state"]["presentation"]["wording"]
    assert "主导" not in bullet


def test_v2_e2e_keeps_literature_work_independent_and_r_supervised():
    """The MVP path must not leak R's boundary into literature screening."""
    client, _ = make_client(); sid = start(client)
    post(client, sid, {
        "text": "我在导师指导下做 Meta 分析，PubMed 检索和文献筛选主要是我自己做的，R 分析老师带着我做。",
        "consent_confirmed": True,
    })
    confirmed = post(client, sid, {"text": "这些都是完整流程。", "consent_confirmed": True})
    responsibilities = {item["activity_id"]: item for item in confirmed["state"]["task_responsibilities"]}
    activities = {item["activity_id"]: item for item in confirmed["state"]["activities"]}
    screening_id = next(item_id for item_id, item in activities.items() if "screen_studies" in item["components"]["actions"])
    analysis_id = next(item_id for item_id, item in activities.items() if "perform_analysis" in item["components"]["actions"])
    assert responsibilities[screening_id]["execution_mode"] == "independent"
    assert responsibilities[analysis_id]["execution_mode"] == "supervised"

    composed = post(client, sid, {"text": "保研"})
    assert "按保研方向，我先建议这样写：" in composed["assistant_message"]
    claims = composed["state"]["claims"]
    screening_claim = next(claim for claim in claims if screening_id in claim["dependency_refs"]["activity_ids"])
    analysis_claim = next(claim for claim in claims if analysis_id in claim["dependency_refs"]["activity_ids"])
    assert screening_claim["dependency_refs"]["responsibility_ids"] == [responsibilities[screening_id]["responsibility_id"]]
    assert analysis_claim["dependency_refs"]["responsibility_ids"] == [responsibilities[analysis_id]["responsibility_id"]]
    assert "在指导下" not in screening_claim["wording"]
    assert "独立" not in analysis_claim["wording"]

    rewritten = post(client, sid, {"text": "按保研方向写得专业一点，但别显得我主导整个项目"})
    assert "可以，我把语气调整得更专业" in rewritten["assistant_message"]
    right_side = rewritten["resume_document"]["research_experience"][0]["bullets"]
    assert right_side[0]["text"] in rewritten["assistant_message"]


def test_free_conversation_reply_does_not_change_state_or_require_workflow_action():
    client, _ = make_client(); sid = start(client)
    before = post(client, sid, {"text": "这是什么意思？"})
    assert "不会增加" in before["assistant_message"]
    assert not before["state"]["evidence_records"]
    assert before["state"]["canonical_experience"] is None


def test_presentation_writer_combines_ready_atomic_claims_into_one_traceable_sentence():
    client, _ = make_client(); sid = start(client)
    post(client, sid, {"text": "我在导师指导下做 Meta 分析，PubMed 检索和文献筛选主要是我自己做的，R 分析老师带着我做。", "consent_confirmed": True})
    post(client, sid, {"text": "这些都是完整流程。", "consent_confirmed": True})
    post(client, sid, {"text": "保研"})
    result = post(client, sid, {"text": "给我完整的一句话"})
    presentation = result["state"]["presentation"]
    assert presentation["status"] == "ready"
    assert "独立完成" in presentation["wording"]
    assert "导师指导下" in presentation["wording"]
    assert set(presentation["source_claim_ids"]) == {claim["claim_id"] for claim in result["state"]["claims"]}
    assert result["resume_document"]["research_experience"][0]["bullets"][0]["text"] == presentation["wording"]


def test_v2_runtime_trace_and_runtime_info_do_not_expose_raw_model_data():
    client, _ = make_client(); sid = start(client)
    response = post(client, sid, {"text": "这是什么意思？"})
    trace = response["runtime_trace"]
    assert trace["model_plan_called"] is True
    assert trace["model_plan_status"] == "success"
    assert trace["proposed_action_types"] == []
    assert trace["final_response_source"] == "model/free_chat"
    assert "raw" not in trace

    info = client.get("/api/runtime-info").get_json()
    assert info["conversation_v2_version"] == "runtime-observability-v1"
    assert info["git_head_sha"]
    assert "api_key" not in info
