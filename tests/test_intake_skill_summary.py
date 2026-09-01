from __future__ import annotations

import json

from medical_career_agent.api import create_app
from medical_career_agent.services.intake_summary_validation import IntakeSummaryValidationService


MATERIAL = "在导师指导下参与系统综述，使用 PubMed 检索文献并完成文献筛选。"


class SkillSummaryGateway:
    def __init__(
        self, *, fact_refs: list[str] | None = None, fail: bool = False,
        selected_question_id: str = "responsibility_boundary",
    ):
        self.calls = []
        self.fact_refs = fact_refs or ["actions:retrieve_literature", "actions:screen_studies", "tools:pubmed"]
        self.fail = fail
        self.selected_question_id = selected_question_id

    def generate(self, *, task, context):
        self.calls.append((task, context))
        if task == "resume_intake_skill_summary":
            if self.fail:
                raise RuntimeError("model unavailable")
            cards = context.get("allowed_question_cards") or []
            card = next(
                (item for item in cards if item.get("question_id") == self.selected_question_id),
                cards[0] if cards else {},
            )
            option_ids = [item["id"] for item in card.get("options", [])[:2]]
            return json.dumps({
                "summary": {
                    "fact_refs": self.fact_refs,
                    "evidence_quotes": [MATERIAL],
                },
                "next_question": {
                    "question_id": card.get("question_id"),
                    "text": "接下来请只确认：这些具体步骤中，哪些由你实际完成？",
                    "reason": "需要把参与项目拆成可核验的个人行动。",
                    "recommended_option_ids": option_ids,
                },
            }, ensure_ascii=False)
        raise AssertionError(f"unexpected model task: {task}")


def test_obvious_fact_turn_uses_one_skill_summary_call_and_applies_only_allowed_question():
    gateway = SkillSummaryGateway()
    client = create_app(model_gateway=gateway, load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    response = client.post(
        f"/api/conversations/{session_id}/messages",
        json={
            "action": "submit_experience", "text": MATERIAL, "consent_confirmed": True,
            "experience_identity": {
                "project_name": "系统综述项目", "organization": "某课题组",
                "role_title": "课题成员", "period": {},
            },
        },
    ).get_json()

    summary_calls = [context for task, context in gateway.calls if task == "resume_intake_skill_summary"]
    assert len(summary_calls) == 1
    assert not any(task == "resume_conversation_turn_plan" for task, _ in gateway.calls)
    assert not any(task == "resume_activity_proposals" for task, _ in gateway.calls)
    assert response["state"]["intake_model"]["status"] == "validated"
    assert response["state"]["intake_model"]["summary_source"] == "llm_validated"
    assert response["state"]["question_card"]["question_id"] == "responsibility_boundary"
    restored = client.get(f"/api/conversations/{session_id}").get_json()
    assert restored["state"]["question_card"]["question_id"] == "responsibility_boundary"
    assert not response["state"]["question_card"]["text"].startswith("接下来请只确认")
    assert set(response["state"]["question_card"]["recommended_option_ids"]).issubset(
        {item["id"] for item in response["state"]["question_card"]["options"]}
    )
    context = summary_calls[0]
    assert len(context["active_evidence"]) == 1
    assert context["active_evidence"][0]["source_text"] == MATERIAL
    assert "系统综述项目" not in str(context["active_evidence"])
    assert "actions:screen_studies" in context["allowed_fact_refs"]
    assert len(context["allowed_question_cards"]) >= 2
    assert "never create or confirm a fact" in context["instruction"]


def test_structured_option_ids_and_free_text_reach_skill_summary_without_becoming_authority():
    gateway = SkillSummaryGateway()
    client = create_app(model_gateway=gateway, load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    first = client.post(f"/api/conversations/{session_id}/messages", json={"action": "submit_experience", "text": MATERIAL, "consent_confirmed": True}).get_json()
    selected_id = first["state"]["question_card"]["options"][0]["id"]

    response = client.post(
        f"/api/conversations/{session_id}/messages",
        json={
            "action": "update_facts", "text": "我还使用 R。",
            "selected_option_ids": [selected_id, "forged-option"], "free_text": "用于敏感性分析。",
            "display_text": "我还使用 R；用于敏感性分析。", "consent_confirmed": True,
        },
    ).get_json()

    context = [context for task, context in gateway.calls if task == "resume_intake_skill_summary"][-1]
    assert context["user_answer"]["selected_option_ids"] == [selected_id]
    assert context["user_answer"]["free_text"] == "用于敏感性分析。"
    assert response["state"]["evidence_records"][-1]["source_text"] == "我还使用 R。"
    assert response["state"]["structured_answers"][-1]["selected_option_ids"] == [selected_id]


def test_unknown_fact_ref_is_rejected():
    rejected_client = create_app(
        model_gateway=SkillSummaryGateway(fact_refs=["tools:invented_tool"]),
        load_model_from_environment=False,
    ).test_client()
    rejected_session = rejected_client.post("/api/conversations", json={}).get_json()["session_id"]
    rejected = rejected_client.post(
        f"/api/conversations/{rejected_session}/messages",
        json={"action": "submit_experience", "text": MATERIAL, "consent_confirmed": True},
    ).get_json()
    assert rejected["state"]["intake_model"]["status"] == "rejected"
    assert rejected["state"]["evidence_records"][0]["source_text"] == MATERIAL


def test_model_failure_is_visible_and_does_not_block_deterministic_question():
    gateway = SkillSummaryGateway(fail=True)
    client = create_app(model_gateway=gateway, load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    response = client.post(
        f"/api/conversations/{session_id}/messages",
        json={"action": "submit_experience", "text": MATERIAL, "consent_confirmed": True},
    ).get_json()

    assert response["state"]["intake_model"]["status"] == "failed"
    assert "原始回答已保留" in response["state"]["intake_model"]["error"]
    assert response["state"]["question_card"]
    assert response["state"]["evidence_records"][0]["source_text"] == MATERIAL


def test_model_responsibility_prose_and_empty_quote_cannot_reach_rendered_summary():
    result = IntakeSummaryValidationService.validate(
        candidate={
            "summary": {
                "text": "我主导了系统综述。", "fact_refs": ["methods:systematic_review"],
                "evidence_quotes": ["我参与了系统综述。"],
            },
            "next_question": None,
        },
        extracted_facts={"methods": ["systematic_review"]},
        evidence_texts=["我参与了系统综述。"],
        question_cards=[],
    )

    assert result["status"] == "validated"
    assert "主导" not in result["summary"]

    empty_quote = IntakeSummaryValidationService.validate(
        candidate={
            "summary": {"fact_refs": ["methods:systematic_review"], "evidence_quotes": [""]},
            "next_question": None,
        },
        extracted_facts={"methods": ["systematic_review"]},
        evidence_texts=["我参与了系统综述。"],
        question_cards=[],
    )
    assert empty_quote["status"] == "rejected"


def test_model_cannot_select_a_question_or_options_outside_backend_candidates():
    for next_question in (
        {"question_id": "forged_question", "recommended_option_ids": []},
        {"question_id": "research_steps", "recommended_option_ids": ["forged_option"]},
    ):
        result = IntakeSummaryValidationService.validate(
            candidate={
                "summary": {
                    "fact_refs": ["methods:systematic_review"],
                    "evidence_quotes": ["我参与了系统综述。"],
                },
                "next_question": next_question,
            },
            extracted_facts={"methods": ["systematic_review"]},
            evidence_texts=["我参与了系统综述。"],
            question_cards=[{
                "question_id": "research_steps",
                "options": [{"id": "screening"}],
            }],
        )

        assert result["status"] == "validated"
        assert result["next_question"] is None


def test_legacy_natural_language_intake_is_deterministic_and_never_calls_model():
    class ForbiddenGateway:
        def __init__(self):
            self.calls = []

        def generate(self, *, task, context):
            self.calls.append((task, context))
            raise AssertionError("legacy intake must not call the model")

    gateway = ForbiddenGateway()
    client = create_app(model_gateway=gateway, load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]

    response = client.post(
        f"/api/conversations/{session_id}/messages",
        json={"text": MATERIAL, "consent_confirmed": True},
    ).get_json()

    assert gateway.calls == []
    assert response["stage"] == "fact_confirmation"
    assert response["state"]["evidence_records"][0]["source_text"] == MATERIAL
    assert response["assistant_message"].startswith("我已提取出候选事实")
