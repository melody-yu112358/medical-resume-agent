from pathlib import Path

from medical_career_agent.api import create_app
from medical_career_agent.services.question_guidance import QuestionGuidanceService


def test_database_question_exposes_rich_multiple_choice_without_asserting_facts():
    card = QuestionGuidanceService.build(
        "使用了哪些数据库进行文献检索？",
        stage="fact_confirmation",
    )

    assert card["question_id"] == "databases_used"
    assert card["selection_mode"] == "multiple"
    assert len(card["options"]) >= 8
    assert {item["id"] for item in card["options"]} >= {"pubmed", "embase", "cochrane", "unknown"}
    assert all(item["answer_text"] for item in card["options"])


def test_publication_question_is_single_choice_and_keeps_unknown_available():
    card = QuestionGuidanceService.build(
        "这个项目是否有发表计划或已发表？",
        stage="fact_confirmation",
    )

    assert card["question_id"] == "publication_status"
    assert card["selection_mode"] == "single"
    assert "unknown" in {item["id"] for item in card["options"]}


def test_question_card_is_absent_outside_fact_confirmation():
    assert QuestionGuidanceService.build("使用了哪些数据库？", stage="intake") is None
    assert QuestionGuidanceService.build(None, stage="fact_confirmation") is None


def test_conversation_returns_and_restores_one_structured_question_card():
    client = create_app(load_model_from_environment=False).test_client()
    created = client.post("/api/conversations", json={}).get_json()
    session_id = created["session_id"]

    response = client.post(
        f"/api/conversations/{session_id}/messages",
        json={"text": "参与心血管系统综述项目。", "consent_confirmed": True},
    )
    assert response.status_code == 200
    state = response.get_json()["state"]
    assistant_message = response.get_json()["assistant_message"]
    card = state["question_card"]
    assert card["text"] == state["pending_questions"][0]
    assert card["options"]
    assert f"请先回答：{state['pending_questions'][0]}" in assistant_message
    if len(state["pending_questions"]) > 1:
        assert state["pending_questions"][1] not in assistant_message

    restored = client.get(f"/api/conversations/{session_id}").get_json()["state"]
    assert restored["question_card"] == card


def test_workspace_submits_selected_answer_text_to_existing_update_path():
    script = (Path(__file__).resolve().parents[1] / "demo" / "resume-agent" / "app.js").read_text(encoding="utf-8")

    assert "data-question-option" in script
    assert "selection_mode" in script
    assert "option.answer_text" in script
    assert 'action: "update_facts"' in script
    assert "selectedQuestionOptions" in script
    assert "selected_option_ids" in script
    assert "renderIntakeModelSummary" in script


def test_answered_multi_selects_survive_full_evidence_replan_without_repeating_question():
    client = create_app(load_model_from_environment=False).test_client()
    session_id = client.post("/api/conversations", json={}).get_json()["session_id"]
    first = client.post(
        f"/api/conversations/{session_id}/messages",
        json={
            "text": "参与 Meta 分析并执行文献检索。",
            "consent_confirmed": True,
        },
    ).get_json()
    assert first["state"]["question_card"]["question_id"] == "databases_used"

    databases = client.post(
        f"/api/conversations/{session_id}/messages",
        json={
            "action": "update_facts",
            "text": "我使用了 Web of Science；我使用了中国知网 CNKI。",
            "selected_option_ids": ["web_of_science", "cnki"],
            "consent_confirmed": True,
        },
    ).get_json()
    facts = databases["state"]["extracted_draft"]["extracted_facts"]
    assert {"web_of_science", "cnki"}.issubset(facts["tools"])
    assert "meta_analysis" in facts["methods"]
    assert "retrieve_literature" in facts["actions"]
    assert databases["state"]["question_card"]["question_id"] == "research_steps"

    steps = client.post(
        f"/api/conversations/{session_id}/messages",
        json={
            "action": "update_facts",
            "text": "我参与设计检索式；我参与质量评价或偏倚评估。",
            "selected_option_ids": ["search_strategy", "quality_assessment"],
            "consent_confirmed": True,
        },
    ).get_json()
    facts = steps["state"]["extracted_draft"]["extracted_facts"]
    assert {"design_search_strategy", "assess_quality"}.issubset(facts["actions"])
    assert steps["state"]["question_card"]["question_id"] not in {
        "databases_used", "research_steps",
    }
