import json
from pathlib import Path
import sys


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.conversation_model_gateway import ModelGatewayConversationGateway


class RecordingGateway:
    def __init__(self):
        self.calls = []

    def generate(self, *, task, context):
        self.calls.append((task, context))
        return json.dumps({"wording": "x", "used_facts": [], "dependency_refs": {}, "evidence_ids": []})


def test_rewrite_prompt_contract_defines_distinct_safe_tiers():
    recorder = RecordingGateway()
    gateway = ModelGatewayConversationGateway(recorder)

    gateway.rewrite_claim(source_claim={}, canonical_experience={}, tone="Professional", instruction="专业一点")

    instruction = recorder.calls[0][1]["instruction"]
    assert "Conservative" in instruction
    assert "Professional" in instruction
    assert "High-impact" in instruction
    assert "verbatim unchanged" in instruction
    assert "主导" in instruction


def test_intake_summary_prompt_receives_skill_constraints_and_backend_whitelists():
    recorder = RecordingGateway()

    ModelGatewayConversationGateway(recorder).summarize_intake_turn(
        text="我使用了 PubMed。", selected_option_ids=["pubmed"], free_text="",
        session_context={
            "active_evidence": [{"evidence_id": "ev_001", "source_text": "我使用了 PubMed。"}],
            "extracted_facts": {"tools": ["pubmed"]}, "allowed_fact_refs": ["tools:pubmed"],
            "confirmed_facts": None, "previous_questions": [],
        },
        allowed_question_cards=[
            {"question_id": "research_steps", "options": [{"id": "screening"}]},
            {"question_id": "outputs", "options": [{"id": "analysis_tables"}]},
        ],
    )

    task, context = recorder.calls[0]
    assert task == "resume_intake_skill_summary"
    assert context["user_answer"]["selected_option_ids"] == ["pubmed"]
    assert context["allowed_fact_refs"] == ["tools:pubmed"]
    assert [item["question_id"] for item in context["allowed_question_cards"]] == [
        "research_steps", "outputs",
    ]
    assert "single highest-value unresolved gap" in context["instruction"]
    assert "Medical Resume Skill Stage 1" in context["instruction"]
