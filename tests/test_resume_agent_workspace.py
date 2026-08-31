from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from medical_career_agent.api import create_app
from medical_career_agent.services.experience_draft import ExperienceDraftService
from medical_career_agent.services.resume_conversation_agent import ResumeConversationAgent


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = "在导师指导下参与 Meta 分析，使用 R 完成统计分析，并使用 PubMed 检索文献。"


def test_live_acceptance_script_imports_current_checkout_without_installation():
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        environment.pop(name, None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "accept_live_skill_intake.py")],
        cwd=ROOT, env=environment, capture_output=True, text=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "missing environment variable: LLM_BASE_URL" in output
    assert "ModuleNotFoundError" not in output


def test_live_acceptance_covers_bounded_tiers_and_user_edit_reaudit():
    script = (ROOT / "scripts" / "accept_live_skill_intake.py").read_text(
        encoding="utf-8"
    )

    assert "CALL_LIMIT = 5" in script
    assert '"action": "generate_resume_tiers"' in script
    assert '"resume_experience_tier_rewrite"' in script
    assert '"all_tier_candidates_accounted_for"' in script
    assert '"each_tier_has_a_safe_rewrite"' in script
    assert '"rejected_candidates_never_selected"' in script
    assert '"three_final_tiers_substantively_distinct"' in script
    assert '"three_distinct_tier_wordings_per_claim"' in script
    assert '"rejected_tier_gates"' in script
    assert '{"extract_data", "perform_analysis"}' in script
    assert '"action": "reopen_audit"' in script
    assert '"action": "edit_wording"' in script
    assert 'delivery_data["edit_status"] == "user-edited"' in script


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
    sample = _message(client, session_id, {"action": "select_role_packs", "role_packs": [role_pack]})
    assert sample["stage"] == "representative_sample"
    composed = _message(client, session_id, {"action": "approve_representative_sample"})
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


def test_user_can_defer_an_incomplete_experience_without_losing_raw_input():
    client = create_app(load_model_from_environment=False).test_client()
    created = client.post("/api/conversations", json={}).get_json()
    session_id = created["session_id"]
    intake = _message(client, session_id, {
        "text": "参加过一次科研训练，但暂时不记得具体任务。",
        "consent_confirmed": True,
        "experience_identity": {"experience_type": "research", "project_name": "科研训练"},
    })
    assert intake["stage"] == "fact_confirmation"

    deferred = _message(client, session_id, {"action": "discard_current_experience"})

    assert deferred["stage"] == "intake"
    assert deferred["state"]["active_experience_id"] is None
    assert deferred["state"]["active_experience_evidence_ids"] == []
    assert deferred["state"]["extracted_draft"] is None
    assert any("参加过一次科研训练" in item for item in deferred["state"]["raw_user_texts"])
    assert deferred["state"]["confirmed_experiences"] == []


def test_sparse_experience_cannot_skip_skill_questions_and_generate_one_line():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    intake = _message(client, session_id, {
        "text": "完成文献筛选", "consent_confirmed": True,
        "experience_identity": {
            "experience_type": "research", "project_name": "心血管 Meta 分析",
            "role_title": "课题成员",
        },
    })
    card = intake["state"]["question_card"]
    supplemented = _message(client, session_id, {
        "action": "update_facts", "text": "相关工作由我独立完成。",
        "display_text": "相关工作由我独立完成。", "free_text": "",
        "question_id": card["question_id"], "selected_option_ids": [],
    })
    proposals = [
        {
            "evidence_quote": item["evidence_quote"],
            "components": item["components"],
            "ownership_level": "contributed", "execution_mode": "independent",
            "coverage": "full", "scope_note": None,
        }
        for item in supplemented["state"]["activity_proposals"]
        if item["status"] == "needs_user_confirmation"
    ]

    blocked = _message(client, session_id, {
        "action": "confirm_activity_proposals", "activity_proposals": proposals,
        "proposal_ids": [],
    })

    assert blocked["stage"] == "fact_confirmation"
    assert blocked["state"]["confirmed_experiences"] == []
    assert blocked["state"]["question_card"]
    assert "信息还不足以形成专业简历" in blocked["assistant_message"]

    state = blocked["state"]
    asked_question_ids = []
    for _ in range(10):
        card = state.get("question_card")
        if not card:
            break
        asked_question_ids.append(card["question_id"])
        unknown = next(item for item in card["options"] if item["id"] == "unknown")
        state = _message(client, session_id, {
            "action": "update_facts", "text": unknown["answer_text"],
            "display_text": unknown["label"], "free_text": "",
            "question_id": card["question_id"],
            "selected_option_ids": ["unknown"],
        })["state"]
    assert len(asked_question_ids) == len(set(asked_question_ids)), asked_question_ids
    assert state["pending_questions"] == [], asked_question_ids
    assert state["question_card"] is None

    proposals = [
        {
            "evidence_quote": item["evidence_quote"],
            "components": item["components"],
            "ownership_level": "contributed", "execution_mode": "independent",
            "coverage": "full", "scope_note": None,
        }
        for item in state["activity_proposals"]
        if item["status"] == "needs_user_confirmation"
    ]
    finished = _message(client, session_id, {
        "action": "confirm_activity_proposals", "activity_proposals": proposals,
        "proposal_ids": [],
    })
    assert finished["stage"] == "representative_sample"


def test_new_experience_does_not_inherit_previous_question_answers():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    first = _message(client, session_id, {
        "text": "完成文献筛选", "consent_confirmed": True,
    })
    first_card = first["state"]["question_card"]
    unknown = next(item for item in first_card["options"] if item["id"] == "unknown")
    answered = _message(client, session_id, {
        "action": "update_facts", "text": unknown["answer_text"],
        "display_text": unknown["label"], "free_text": "",
        "question_id": first_card["question_id"],
        "selected_option_ids": ["unknown"],
    })
    proposals = [
        {
            "evidence_quote": item["evidence_quote"],
            "components": item["components"],
            "ownership_level": "contributed", "execution_mode": "shared",
            "coverage": "partial", "scope_note": None,
        }
        for item in answered["state"]["activity_proposals"]
        if item["status"] == "needs_user_confirmation"
    ]
    confirmed = _message(client, session_id, {
        "action": "confirm_activity_proposals", "activity_proposals": proposals,
        "proposal_ids": [], "accept_sparse_result": True,
    })
    assert confirmed["stage"] == "representative_sample"
    _message(client, session_id, {"action": "start_new_experience"})

    second = _message(client, session_id, {
        "text": "完成文献筛选", "consent_confirmed": True,
    })

    assert second["state"]["question_card"]["question_id"] == first_card["question_id"]
    answers = second["state"]["structured_answers"]
    assert len({item.get("experience_key") for item in answers}) == 1


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


def test_delivery_edit_returns_to_audit_and_exports_user_edited_status():
    client = create_app(load_model_from_environment=False).test_client()
    session_id, delivered = _delivery_conversation(client)
    claim = delivered["state"]["generated_claims"][0]

    reopened = _message(client, session_id, {"action": "reopen_audit"})
    edited = _message(client, session_id, {
        "action": "edit_wording", "claim_id": claim["claim_id"],
        "wording": claim["wording"],
    })
    redelivered = _message(client, session_id, {"action": "accept_bullets"})
    exported = client.post(f"/api/conversations/{session_id}/export", json={})

    assert reopened["stage"] == "factual_audit"
    assert edited["stage"] == "factual_audit"
    assert redelivered["stage"] == "delivery"
    assert exported.status_code == 200
    data = json.loads(exported.get_json()["files"]["resume-data.json"])
    assert data["edit_status"] == "user-edited"


def test_unready_delivery_edit_blocks_redelivery_and_export():
    client = create_app(load_model_from_environment=False).test_client()
    session_id, delivered = _delivery_conversation(client)
    claim = delivered["state"]["generated_claims"][0]
    _message(client, session_id, {"action": "reopen_audit"})

    edited = _message(client, session_id, {
        "action": "edit_wording", "claim_id": claim["claim_id"],
        "wording": "主导 999 项临床研究并获得国际大奖。",
    })
    refused = _message(client, session_id, {"action": "accept_bullets"})
    exported = client.post(f"/api/conversations/{session_id}/export", json={})

    assert edited["stage"] == "factual_audit"
    assert refused["stage"] == "factual_audit"
    assert "仍有基础要点未通过" in refused["assistant_message"]
    assert exported.status_code == 400


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
    workspace_css = (ROOT / "demo/resume-agent/workspace.css").read_text(encoding="utf-8")

    assert "简历预览" in html_text
    assert "简历进度" in html_text
    assert "打开旧版 Resume Beta" not in html_text
    assert '<div id="workspace"></div>' in html_text
    assert 'role="status" aria-live="polite"' in html_text
    assert "workspace.css" in html_text
    assert "reset-flow.js" in html_text
    for action in (
        "confirm_activity_proposals", "select_role_packs",
        "edit_wording", "rewrite_claim", "accept_bullets", "answer_candidate_profile",
        "select_rewrite_candidate", "select_resume_tier", "approve_representative_sample",
        "confirm_candidate_profile", "start_new_experience", "discard_current_experience",
        "select_experience", "submit_experience",
    ):
        assert action in script
    assert "/api/conversations/" in script
    assert 'method: "DELETE"' in script
    assert "旧会话删除失败，当前会话仍保留，未创建新简历" in script
    assert "positioning" not in script
    assert "localStorage" in script
    assert "基础资料与教育背景" in script
    assert "荣誉奖励" in script
    assert "语言能力" in script
    assert "证书与培训" in script
    assert "研究兴趣" in script
    assert "简历完整性盘点" in script
    assert "item.canonical_experience?.identity?.experience_type" in script
    assert "论文与学术成果" in script
    assert "ranking_or_gpa" in script
    assert 'label: "聊经历"' in script
    assert 'label: "定表达"' in script
    assert 'label: "完成简历"' in script
    assert 'internalStages: ["intake", "fact_confirmation"]' in script
    assert 'internalStages: ["representative_sample", "composition"]' in script
    assert 'internalStages: ["factual_audit", "delivery"]' in script
    assert "contract.stages.map" not in script
    assert 'visibleStage.id === "conversation"' in script
    assert "已了解的你" in script
    assert "已自动保存到本机" in script
    assert "系统目前了解的信息" in script
    assert "为什么问这个？" in script
    assert "查看系统识别的候选事实" in script
    assert 'class="secondary" type="button">核对完成' in script
    assert "documentData.education" in script
    assert "basics.summary" in script
    assert "documentData.skills" in script
    assert "研究方法与技能" in script
    assert "experience_identity" in script
    assert "experienceName" in script
    assert "experienceType" in script
    assert "校园与领导力" in script
    assert "志愿服务" in script
    assert "experienceOrganization" in script
    assert "experienceRole" in script
    assert "选择完整简历版本" in script
    assert "应用到该档" in script
    assert "confirmed_experiences" in script
    assert "添加另一段经历" in script
    assert "停止追问，核对已有活动" in script
    assert "AI 服务异常 · 不是你的信息不足" in script
    assert "项目由导师指导，不等于每项任务都“在指导下完成”" in script
    assert "请选择本人责任" in script
    assert "请为每项活动明确选择本人责任、执行方式和完成范围" in script
    assert "你的回答会保存在本机 session" in script
    assert 'if ($("#candidateName") && $("#candidateContact")) saveBasicsAndPreview();' in script
    assert "window.print" in script
    assert "button:focus-visible" in workspace_css
    assert "[hidden] { display: none !important; }" in workspace_css
    assert "prefers-reduced-motion" in workspace_css
    assert "forced-colors" in workspace_css
    assert ".conversation-mode .preview-pane { display: none; }" in workspace_css
    assert ".delivery-mode .paper" in workspace_css
    assert "overflow: visible" in workspace_css

    config = create_app(load_model_from_environment=False).test_client().get(
        "/api/resume-agent/config"
    ).get_json()
    frontend_label_ids = set(config["fact_labels"])
    displayed_fact_ids = (
        set(ExperienceDraftService.ACTION_PATTERNS)
        | set(ExperienceDraftService.METHOD_PATTERNS)
        | set(ExperienceDraftService.TECHNIQUE_PATTERNS)
        | {item_id for _, item_id in ExperienceDraftService.TOOL_PATTERNS}
        | set(ExperienceDraftService.COLLABORATION_PATTERNS)
        | set(ExperienceDraftService.ARTIFACT_PATTERNS)
    )
    assert displayed_fact_ids <= frontend_label_ids
    assert config["fact_labels"]["stata"] == "Stata"
    assert config["fact_labels"]["analysis_figures"] == "分析图表"
    assert "const labels = {" not in script
    assert "labels = contract.fact_labels || {}" in script


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
    assert "尚未重新事实审计" in package_editor
    assert "-unaudited-draft" in package_editor


def test_workflow_contract_is_package_owned_and_kept_in_sync_with_skill_bundle():
    api_source = (ROOT / "src/medical_career_agent/api.py").read_text(encoding="utf-8")
    package_contract = (
        ROOT / "src/medical_career_agent/assets/workflow-contract.json"
    ).read_text(encoding="utf-8")
    skill_contract = (
        ROOT
        / "skill-lite/medical-resume-skill/references/workflow-contract.json"
    ).read_text(encoding="utf-8")

    contract = json.loads(package_contract)
    dispatched_actions = set(re.findall(
        r'action == "([^"]+)"', inspect.getsource(ResumeConversationAgent.handle_message),
    ))

    assert "skill-lite" not in api_source
    assert contract == json.loads(skill_contract)
    assert set(contract["actions"]) - dispatched_actions == {
        "create_conversation", "provide_facts",
    }
    assert dispatched_actions <= set(contract["actions"])
    assert contract["rules"]["maximum_questions_per_round"] == 1
