from __future__ import annotations

import json
from pathlib import Path

from medical_career_agent.api import create_app


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = "在导师指导下参与 Meta 分析，使用 R 完成统计分析，并使用 PubMed 检索文献。"


def _message(client, session_id: str, payload: dict):
    response = client.post(f"/api/conversations/{session_id}/messages", json=payload)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _delivery_conversation(client, role_pack="doctoral_v1"):
    created = client.post("/api/conversations", json={})
    assert created.status_code == 201
    session_id = created.get_json()["session_id"]
    intake = _message(client, session_id, {"text": MATERIAL, "consent_confirmed": True})
    proposals = intake["state"]["activity_proposals"]
    assert proposals
    updated = []
    for proposal in proposals:
        updated.append({
            "evidence_quote": proposal["evidence_quote"],
            "components": proposal["components"],
            "ownership_level": "contributed",
            "execution_mode": "supervised",
            "coverage": "partial",
            "scope_note": "按既定流程完成部分步骤",
        })
    confirmed = _message(client, session_id, {
        "action": "confirm_activity_proposals", "activity_proposals": updated,
        "proposal_ids": [],
    })
    assert confirmed["stage"] == "representative_sample"
    composed = _message(client, session_id, {"action": "select_role_packs", "role_packs": [role_pack]})
    assert composed["stage"] == "factual_audit"
    assert composed["audit_status"]["ready"] > 0
    delivered = _message(client, session_id, {"action": "accept_bullets"})
    assert delivered["stage"] == "delivery"
    return session_id, delivered


def test_skill_contract_and_primary_workspace_are_connected():
    client = create_app(load_model_from_environment=False).test_client()

    config = client.get("/api/resume-agent/config")
    assert config.status_code == 200
    assert config.get_json()["schema_version"] == "medical-resume-workflow-v1"
    assert [stage["id"] for stage in config.get_json()["stages"]] == [
        "intake", "fact_confirmation", "representative_sample", "composition", "factual_audit", "delivery"
    ]


def test_clinical_operations_runs_contract_workspace_claim_gate_and_delivery():
    client = create_app(load_model_from_environment=False).test_client()
    config = client.get("/api/resume-agent/config").get_json()

    assert {"id": "clinical_operations", "label": "临床运营 / 临床项目协调", "role_pack": "clinical_operations_v1"} in config["targets"]
    session_id, delivered = _delivery_conversation(client, "clinical_operations_v1")

    assert delivered["state"]["selected_role_packs"] == ["clinical_operations_v1"]
    assert delivered["audit_status"]["ready"] > 0
    exported = client.post(f"/api/conversations/{session_id}/export", json={})
    assert exported.status_code == 200
    assert "临床运营与试验协调" in exported.get_json()["files"]["resume.md"]
    root = client.get("/")
    assert root.status_code == 302
    assert root.headers["Location"] == "/demo/resume-agent/index.html"
    assert client.get("/demo/resume-agent/index.html").status_code == 200


def test_existing_conversation_agent_reaches_export_without_a_second_pipeline():
    client = create_app(load_model_from_environment=False).test_client()
    session_id, delivered = _delivery_conversation(client)

    canonical = delivered["state"]["confirmed_canonical_experience"]
    assert canonical["schema_version"] == "canonical-experience-v2"
    assert canonical["task_responsibilities"]
    response = client.post(
        f"/api/conversations/{session_id}/export",
        json={
            "theme": "academic-green",
            "basics": {"name": "测试候选人", "contact": "test@example.invalid", "positioning": "未经审计的强定位"},
        },
    )
    assert response.status_code == 200, response.get_json()
    bundle = response.get_json()
    assert set(bundle["files"]) == {
        "resume.md", "resume.html", "resume-editor.html", "resume-data.json",
        "evidence-summary.json", "rewrite-comparison.md", "export-instructions.txt",
    }
    assert "测试候选人" in bundle["files"]["resume.html"]
    assert "学术升学与科研申请" in bundle["files"]["resume.html"]
    assert "doctoral_v1" not in bundle["files"]["resume.html"]
    assert "ACS" not in bundle["files"]["resume.html"]
    assert "45 篇" not in bundle["files"]["resume.html"]
    assert "未经审计的强定位" not in bundle["files"]["resume.md"]
    assert "未经审计的强定位" not in bundle["files"]["resume.html"]
    assert "positioning" not in json.loads(bundle["files"]["resume-data.json"])["basics"]
    assert "## 候选人定位" in bundle["files"]["resume.md"]
    assert "## 研究方法与技能" in bundle["files"]["resume.md"]
    assert "**研究方法：** Meta 分析" in bundle["files"]["resume.md"]
    assert "**文献与证据资源：** PubMed" in bundle["files"]["resume.md"]
    assert bundle["privacy"]["export_written_to_server"] is False
    resume_document = json.loads(bundle["files"]["resume-data.json"])["resume_document"]
    assert resume_document["research_experience"]
    evidence_ids = {item["evidence_id"] for item in resume_document["evidence"]}
    assert resume_document["skills"]
    assert all(set(item["evidence_ids"]) <= evidence_ids for item in resume_document["skills"])
    assert "仅保存在当前浏览器" in bundle["files"]["resume-editor.html"]
    assert "用户确认的原始依据" in bundle["files"]["rewrite-comparison.md"]


def test_export_is_blocked_before_delivery_and_session_delete_cleans_local_files():
    client = create_app(load_model_from_environment=False).test_client()
    created = client.post("/api/conversations", json={}).get_json()
    session_id = created["session_id"]

    blocked = client.post(f"/api/conversations/{session_id}/export", json={})
    assert blocked.status_code == 400
    deleted = client.delete(f"/api/conversations/{session_id}")
    assert deleted.status_code == 200
    assert deleted.get_json()["deleted"] is True
    assert client.get(f"/api/conversations/{session_id}").status_code == 404


def test_accept_bullets_cannot_fake_delivery_before_audit():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    response = _message(client, session_id, {"action": "accept_bullets"})

    assert response["stage"] == "intake"
    assert "尚无可交付" in response["assistant_message"]


def test_claim_cleanup_failure_preserves_conversation(monkeypatch):
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    def fail_cleanup(_ledger, _session_id):
        raise OSError("claim sidecar is locked")

    monkeypatch.setattr(
        "medical_career_agent.api.ClaimLedgerService.cleanup_session_claims",
        fail_cleanup,
    )
    failed = client.delete(f"/api/conversations/{session_id}")

    assert failed.status_code == 500
    assert "failed to delete local conversation" in failed.get_json()["error"]
    assert client.get(f"/api/conversations/{session_id}").status_code == 200


def test_export_rejects_invalid_session_id_and_reports_unknown_valid_id():
    client = create_app(load_model_from_environment=False).test_client()

    invalid = client.post("/api/conversations/bad$id/export", json={})
    assert invalid.status_code == 400
    assert "unsupported characters" in invalid.get_json()["error"]

    unknown = client.post("/api/conversations/missing-session/export", json={})
    assert unknown.status_code == 404
    assert "unknown session_id" in unknown.get_json()["error"]


def test_workspace_assets_expose_v2_confirmation_audit_export_and_cleanup():
    html_text = (ROOT / "demo/resume-agent/index.html").read_text(encoding="utf-8")
    script = (ROOT / "demo/resume-agent/app.js").read_text(encoding="utf-8")

    assert "LIVE A4 PREVIEW" in html_text
    assert "workspace.css" in html_text
    assert "reset-flow.js" in html_text
    for action in (
        "confirm_activity_proposals", "select_role_packs",
        "edit_wording", "rewrite_claim", "accept_bullets", "answer_candidate_profile",
        "confirm_candidate_profile", "start_new_experience", "select_experience", "submit_experience",
    ):
        assert action in script
    assert "/api/conversations/" in script
    assert 'method: "DELETE"' in script
    assert "旧会话删除失败，当前会话仍保留，未创建新简历" in script
    assert "positioning" not in script
    assert "localStorage" in script
    assert "基础资料与教育背景" in script
    assert "documentData.education" in script
    assert "basics.summary" in script
    assert "documentData.skills" in script
    assert "研究方法与技能" in script
    assert "experience_identity" in script
    assert "experienceName" in script
    assert "experienceOrganization" in script
    assert "experienceRole" in script
    assert "confirmed_experiences" in script
    assert "添加另一段经历" in script
    assert "你的回答会保存在本机 session" in script
    assert 'if ($("#candidateName") && $("#candidateContact")) saveBasicsAndPreview();' in script
    assert "window.print" in script


def test_delivery_editor_is_package_owned_and_kept_in_sync_with_skill_bundle():
    service = (
        ROOT / "src/medical_career_agent/services/resume_delivery.py"
    ).read_text(encoding="utf-8")
    package_editor = (
        ROOT / "src/medical_career_agent/assets/resume-editor.html"
    ).read_text(encoding="utf-8")
    skill_editor = (
        ROOT / "skill-lite/medical-resume-skill/assets/resume-editor.html"
    ).read_text(encoding="utf-8")

    assert "skill-lite" not in service
    assert package_editor == skill_editor
    assert "__INITIAL_MARKDOWN_JSON__" in package_editor
