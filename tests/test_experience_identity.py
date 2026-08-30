from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from medical_career_agent.api import create_app


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = "在导师指导下参与 Meta 分析，使用 R 完成统计分析。"
IDENTITY = {
    "project_name": "心血管风险因素 Meta 分析项目",
    "organization": "某大学附属医院课题组",
    "role_title": "课题成员",
    "period": {"start": "2024-03", "end": "2025-01", "ongoing": False},
}


def _message(client, session_id, payload):
    response = client.post(f"/api/conversations/{session_id}/messages", json=payload)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def test_confirmed_experience_identity_reaches_canonical_preview_and_export():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    intake = _message(client, session_id, {
        "action": "submit_experience", "text": MATERIAL,
        "consent_confirmed": True, "experience_identity": IDENTITY,
    })
    identity_evidence = [
        item for item in intake["state"]["evidence_records"]
        if item.get("kind") == "experience_identity"
    ]
    assert len(identity_evidence) == 1
    proposals = intake["state"]["activity_proposals"]
    confirmed = _message(client, session_id, {
        "action": "confirm_activity_proposals", "proposal_ids": [],
        "activity_proposals": [{
            "evidence_quote": item["evidence_quote"], "components": item["components"],
            "ownership_level": "contributed", "execution_mode": "supervised",
            "coverage": "partial", "scope_note": "按既定方案完成部分分析步骤",
        } for item in proposals],
    })

    canonical = confirmed["state"]["confirmed_canonical_experience"]
    assert canonical["identity"] == {**IDENTITY, "evidence_ids": [identity_evidence[0]["evidence_id"]]}
    assert set(canonical["identity"]["evidence_ids"]) <= set(canonical["evidence_ids"])
    canonical_schema = json.loads((ROOT / "schemas/canonical-experience-v2.schema.json").read_text(encoding="utf-8"))
    validate(instance=canonical, schema=canonical_schema)
    assert confirmed["state"]["confirmed_experiences"][0]["label"] == IDENTITY["project_name"]

    composed = _message(client, session_id, {"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
    delivered = _message(client, session_id, {"action": "accept_bullets"})
    assert composed["audit_status"]["ready"] > 0
    document = delivered["state"]["resume_document"]
    experience = document["research_experience"][0]
    assert experience["project_name"] == IDENTITY["project_name"]
    assert experience["organization"] == IDENTITY["organization"]
    assert experience["title"] == IDENTITY["role_title"]
    assert experience["period"] == IDENTITY["period"]
    document_schema = json.loads((ROOT / "schemas/resume_document.schema.json").read_text(encoding="utf-8"))
    validate(instance=document, schema=document_schema)

    bundle = client.post(f"/api/conversations/{session_id}/export", json={}).get_json()["files"]
    for value in (IDENTITY["project_name"], IDENTITY["organization"], IDENTITY["role_title"], "2024-03 - 2025-01"):
        assert value in bundle["resume.md"]
        assert value in bundle["resume.html"]
    assert "待补充" not in bundle["resume.md"]
    assert "### 已确认经历" not in bundle["resume.md"]


@pytest.mark.parametrize("identity,error", [
    ({"project_name": "", "period": {}}, "请填写真实的经历或项目名称"),
    ({"project_name": "研究项目", "period": {"start": "2024-13"}}, "有效的年月"),
    ({"project_name": "研究项目", "period": {"start": "2025-01", "end": "2024-01"}}, "结束时间不能早于开始时间"),
])
def test_invalid_experience_identity_does_not_create_evidence(identity, error):
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    result = _message(client, session_id, {
        "action": "submit_experience", "text": MATERIAL,
        "consent_confirmed": True, "experience_identity": identity,
    })

    assert result["stage"] == "intake"
    assert error in result["assistant_message"]
    assert result["state"]["evidence_records"] == []
    assert result["state"]["active_experience_identity"] is None


def test_experience_identity_is_escaped_in_html_export():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    identity = {**IDENTITY, "project_name": "<script>alert('x')</script>"}
    intake = _message(client, session_id, {
        "action": "submit_experience", "text": MATERIAL,
        "consent_confirmed": True, "experience_identity": identity,
    })
    proposals = intake["state"]["activity_proposals"]
    _message(client, session_id, {
        "action": "confirm_activity_proposals", "proposal_ids": [],
        "activity_proposals": [{
            "evidence_quote": item["evidence_quote"], "components": item["components"],
            "ownership_level": "contributed", "execution_mode": "supervised",
            "coverage": "partial", "scope_note": None,
        } for item in proposals],
    })
    _message(client, session_id, {"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
    _message(client, session_id, {"action": "accept_bullets"})

    html = client.post(f"/api/conversations/{session_id}/export", json={}).get_json()["files"]["resume.html"]
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
