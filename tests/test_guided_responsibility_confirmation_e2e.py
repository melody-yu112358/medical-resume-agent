from __future__ import annotations

import pytest

from medical_career_agent.api import create_app


SOURCE = "我参与系统综述并完成文献筛选。"


def _message(client, session_id: str, payload: dict) -> dict:
    response = client.post(f"/api/conversations/{session_id}/messages", json=payload)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


@pytest.mark.parametrize(
    "guided_answer",
    (
        "相关工作由我独立完成。",
        "我负责其中一个明确模块。",
    ),
)
def test_responsibility_option_remains_pending_until_activity_confirmation(guided_answer: str):
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    _message(client, session_id, {"text": SOURCE, "consent_confirmed": True})
    response = _message(
        client,
        session_id,
        {"action": "update_facts", "text": guided_answer, "consent_confirmed": True},
    )
    state = response["state"]

    assert state["stage"] == "fact_confirmation"
    assert state["confirmed_canonical_experience"] is None
    assert state["generated_claims"] == []
    assert any(item["status"] == "needs_user_confirmation" for item in state["activity_proposals"])


def test_unknown_guided_option_cannot_create_deterministic_ownership_or_fact():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    _message(client, session_id, {"text": SOURCE, "consent_confirmed": True})
    response = _message(
        client,
        session_id,
        {
            "action": "update_facts",
            "text": "这项信息我目前不确定或不记得。",
            "consent_confirmed": True,
        },
    )
    state = response["state"]
    pending = [item for item in state["activity_proposals"] if item["status"] == "needs_user_confirmation"]

    assert state["stage"] == "fact_confirmation"
    assert state["confirmed_canonical_experience"] is None
    assert state["generated_claims"] == []
    assert pending
    assert all(item["ownership_level"] != "owned_component" for item in pending)
    assert all(item["execution_mode"] != "independent" for item in pending)
