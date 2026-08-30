from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from medical_career_agent.api import create_app


MATERIALS = (
    "在导师指导下参与系统综述，使用 PubMed 检索文献并完成文献筛选。",
    "在导师指导下参与医疗数据项目，使用 Python 完成数据清洗和统计分析。",
)


def _message(client, session_id: str, payload: dict) -> dict:
    response = client.post(f"/api/conversations/{session_id}/messages", json=payload)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _confirm_material(client, session_id: str, material: str) -> dict:
    intake = _message(client, session_id, {"text": material, "consent_confirmed": True})
    proposals = intake["state"]["activity_proposals"]
    assert proposals
    updated = [{
        "evidence_quote": item["evidence_quote"], "components": item["components"],
        "ownership_level": "contributed", "execution_mode": "supervised",
        "coverage": "partial", "scope_note": "按既定流程完成部分步骤",
    } for item in proposals]
    _message(client, session_id, {"action": "update_activity_proposals", "activity_proposals": updated})
    confirmed = _message(client, session_id, {"action": "confirm_activity_proposals", "proposal_ids": []})
    assert confirmed["stage"] == "representative_sample"
    return confirmed


def test_two_confirmed_experiences_can_be_added_switched_and_composed_together():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    first = _confirm_material(client, session_id, MATERIALS[0])
    first_entry = first["state"]["confirmed_experiences"][0]
    first_id = first_entry["experience_id"]
    first_evidence = set(first_entry["evidence_ids"])
    assert first_evidence == {"ev_001"}

    started = _message(client, session_id, {"action": "start_new_experience"})
    assert started["stage"] == "intake"
    assert started["state"]["confirmed_canonical_experience"] is None
    assert len(started["state"]["confirmed_experiences"]) == 1

    second = _confirm_material(client, session_id, MATERIALS[1])
    assert len(second["state"]["confirmed_experiences"]) == 2
    second_entry = second["state"]["confirmed_experiences"][1]
    second_id = second_entry["experience_id"]
    second_evidence = set(second_entry["evidence_ids"])
    assert second_evidence == {"ev_002"}
    assert first_evidence.isdisjoint(second_evidence)

    selected_first = _message(client, session_id, {"action": "select_experience", "experience_id": first_id})
    assert selected_first["state"]["active_experience_id"] == first_id
    assert selected_first["state"]["confirmed_canonical_experience"]["experience_id"] == first_id
    selected_second = _message(client, session_id, {"action": "select_experience", "experience_id": second_id})
    assert selected_second["state"]["active_experience_id"] == second_id

    composed = _message(client, session_id, {"action": "select_role_packs", "role_packs": ["doctoral_v1"]})
    assert composed["stage"] == "factual_audit"
    assert {item["experience_id"] for item in composed["state"]["generated_claims"]} == {first_id, second_id}
    document = composed["state"]["resume_document"]
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "resume_document.schema.json").read_text(encoding="utf-8"))
    validate(instance=document, schema=schema)
    assert {item["item_id"] for item in document["research_experience"]} == {first_id, second_id}
    assert all(item["bullets"] for item in document["research_experience"])
    evidence_ids = {item["evidence_id"] for item in document["evidence"]}
    for experience in document["research_experience"]:
        assert set(experience["evidence_ids"]).issubset(evidence_ids)
        for bullet in experience["bullets"]:
            assert set(bullet["evidence_ids"]).issubset(evidence_ids)


def test_new_experience_is_blocked_until_current_experience_is_confirmed():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    response = _message(client, session_id, {"action": "start_new_experience"})

    assert response["stage"] == "intake"
    assert response["state"]["confirmed_experiences"] == []
    assert "先确认当前经历" in response["assistant_message"]
