from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from medical_career_agent.api import create_app
from medical_career_agent.services.resume_delivery import ResumeDeliveryService
from medical_career_agent.services.candidate_profile_intake import (
    CandidateProfileInputError,
    CandidateProfileIntakeService,
)


def _answer_all(client, session_id: str) -> dict:
    answers = {
        "name": "测试同学",
        "email": "student@example.invalid",
        "phone": "13800000000",
        "location": "上海",
        "institution": "示例医科大学",
        "degree": "医学硕士",
        "major": "临床医学",
        "period": {"start": "2023-09", "end": None, "ongoing": True},
    }
    response = None
    for question_id, value in answers.items():
        response = client.post(
            f"/api/conversations/{session_id}/messages",
            json={"action": "answer_candidate_profile", "question_id": question_id, "value": value},
        )
        assert response.status_code == 200
    return response.get_json()


def test_profile_service_asks_one_question_and_keeps_profile_evidence_separate():
    profile = CandidateProfileIntakeService.initial_state()

    assert CandidateProfileIntakeService.current_question(profile)["id"] == "name"
    CandidateProfileIntakeService.answer(profile, question_id="name", value="测试同学")
    assert CandidateProfileIntakeService.current_question(profile)["id"] == "email"
    CandidateProfileIntakeService.answer(profile, question_id="email", value=None, skipped=True)
    assert profile["profile_evidence_records"] == []

    with pytest.raises(CandidateProfileInputError):
        CandidateProfileIntakeService.answer(profile, question_id="institution", value="示例医科大学")


def test_profile_service_rejects_invalid_email_and_required_skip():
    profile = CandidateProfileIntakeService.initial_state()
    with pytest.raises(CandidateProfileInputError):
        CandidateProfileIntakeService.answer(profile, question_id="name", value=None, skipped=True)

    CandidateProfileIntakeService.answer(profile, question_id="name", value="测试同学")
    with pytest.raises(CandidateProfileInputError):
        CandidateProfileIntakeService.answer(profile, question_id="email", value="not-an-email")


def test_empty_optional_period_does_not_create_confirmed_evidence():
    profile = CandidateProfileIntakeService.initial_state()
    values = {
        "name": "测试同学", "email": None, "phone": None, "location": None,
        "institution": "示例医科大学", "degree": None, "major": None,
        "period": {"start": "", "end": "", "ongoing": False},
    }
    for question in CandidateProfileIntakeService.QUESTIONS:
        value = values[question["id"]]
        CandidateProfileIntakeService.answer(
            profile, question_id=question["id"], value=value,
            skipped=value is None,
        )
    CandidateProfileIntakeService.confirm(profile)

    assert profile["answers"]["period"] is None
    assert not any(item["field"] == "period" for item in profile["profile_evidence_records"])


def test_confirmed_profile_persists_and_maps_to_resume_document_and_export():
    client = create_app(load_model_from_environment=False).test_client()
    created = client.post("/api/conversations", json={}).get_json()
    session_id = created["session_id"]
    awaiting = _answer_all(client, session_id)

    assert awaiting["state"]["candidate_profile"]["status"] == "awaiting_confirmation"
    assert awaiting["state"]["evidence_records"] == []
    confirmed = client.post(
        f"/api/conversations/{session_id}/messages",
        json={"action": "confirm_candidate_profile"},
    ).get_json()
    assert confirmed["state"]["candidate_profile"]["status"] == "confirmed"
    assert confirmed["state"]["evidence_records"] == []
    assert confirmed["state"]["candidate_profile"]["profile_evidence_records"]

    restored = client.get(f"/api/conversations/{session_id}").get_json()
    assert restored["state"]["candidate_profile"]["answers"]["institution"] == "示例医科大学"

    material = "在导师指导下参与系统综述，使用 PubMed 检索文献并完成文献筛选。"
    intake = client.post(
        f"/api/conversations/{session_id}/messages",
        json={"text": material, "consent_confirmed": True},
    ).get_json()
    proposals = intake["state"]["activity_proposals"]
    updated = [{
        "evidence_quote": item["evidence_quote"], "components": item["components"],
        "ownership_level": "contributed", "execution_mode": "supervised",
        "coverage": "partial", "scope_note": "按既定流程完成部分步骤",
    } for item in proposals]
    client.post(f"/api/conversations/{session_id}/messages", json={"action": "update_activity_proposals", "activity_proposals": updated})
    client.post(f"/api/conversations/{session_id}/messages", json={"action": "confirm_activity_proposals", "proposal_ids": []})
    client.post(f"/api/conversations/{session_id}/messages", json={"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
    client.post(f"/api/conversations/{session_id}/messages", json={"action": "approve_representative_sample"})
    delivered = client.post(f"/api/conversations/{session_id}/messages", json={"action": "accept_bullets"}).get_json()

    document = delivered["state"]["resume_document"]
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "resume_document.schema.json").read_text(encoding="utf-8"))
    validate(instance=document, schema=schema)
    assert document["basics"]["name"] == "测试同学"
    assert document["education"][0]["institution"] == "示例医科大学"
    profile_ids = {item["evidence_id"] for item in document["evidence"] if item["evidence_id"].startswith("profile_ev_")}
    assert set(document["basics"]["evidence_ids"]).issubset(profile_ids)
    assert set(document["education"][0]["evidence_ids"]).issubset(profile_ids)
    evidence_ids = {item["evidence_id"] for item in document["evidence"]}
    assert set(document["basics"]["evidence_ids"]).issubset(evidence_ids)
    assert set(document["education"][0]["evidence_ids"]).issubset(evidence_ids)
    assert set(document["research_experience"][0]["evidence_ids"]).issubset(evidence_ids)

    bundle = client.post(f"/api/conversations/{session_id}/export", json={"basics": {"name": "错误覆盖名"}}).get_json()
    assert "测试同学" in bundle["files"]["resume.md"]
    assert "示例医科大学" in bundle["files"]["resume.md"]
    assert "错误覆盖名" not in bundle["files"]["resume.md"]
    assert json.loads(bundle["files"]["resume-data.json"])["resume_document"]["education"][0]["major"] == "临床医学"


def test_existing_direct_experience_intake_remains_compatible():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    response = client.post(
        f"/api/conversations/{session_id}/messages",
        json={"text": "参与 Meta 分析并使用 Stata 完成统计分析。", "consent_confirmed": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["stage"] == "fact_confirmation"
    assert payload["state"]["candidate_profile"]["status"] == "collecting"

def test_confirmed_profile_export_rejects_unconfirmed_basics_fallback():
    conversation = {
        "session_id": "profile-boundary",
        "state": {
            "stage": "delivery",
            "candidate_profile": {"status": "confirmed"},
            "resume_document": {
                "basics": {"name": "已确认姓名", "phone": None, "email": None, "location": None},
                "target": {"role": "doctoral_v1"},
                "research_experience": [{"title": "已确认经历", "bullets": [{"text": "完成已确认任务。"}]}],
            },
        },
    }

    bundle = ResumeDeliveryService().build_bundle(
        conversation=conversation,
        basics={"name": "临时覆盖名", "contact": "unconfirmed@example.invalid · 未确认城市"},
    )
    exported = json.loads(bundle["files"]["resume-data.json"])

    assert exported["basics"] == {"name": "已确认姓名", "contact": ""}
    assert "临时覆盖名" not in bundle["files"]["resume.md"]
    assert "unconfirmed@example.invalid" not in bundle["files"]["resume.md"]
    assert "未确认城市" not in bundle["files"]["resume.md"]


def test_profile_ui_discloses_local_session_and_avoids_confirmed_fallback():
    app = (Path(__file__).parents[1] / "demo" / "resume-agent" / "app.js").read_text(encoding="utf-8")

    assert "你的回答会保存在本机 session；确认前不会进入最终简历。" in app
    assert 'const fallbackBasics = profileConfirmed ? {} : savedBasics()' in app
    assert 'const basics = state().candidate_profile?.status === "confirmed" ? {} : savedBasics()' in app
