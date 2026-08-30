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
        return json.dumps({"activity_proposals": []} if task == "resume_activity_proposals" else {"wording": "x", "used_facts": [], "dependency_refs": {}, "evidence_ids": []})


def test_activity_proposal_prompt_contract_covers_real_eval_failures():
    recorder = RecordingGateway()
    gateway = ModelGatewayConversationGateway(recorder)

    gateway.propose_activities(text="示例", extracted_facts={"actions": [], "methods": [], "tools": [], "techniques": [], "objects": [], "artifacts": []})

    instruction = recorder.calls[0][1]["instruction"]
    assert "actions:retrieve_literature" in instruction
    assert "requests exaggeration" in instruction
    assert "uncertain outcome" in instruction
    assert "guideline review" in instruction
    assert "do not mean partial" in instruction
    assert "mentor defining a plan" in instruction
    assert "unknown" in recorder.calls[0][1]["execution_modes"]


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


def test_turn_plan_filters_actions_to_the_allow_list():
    class PlanGateway:
        def generate(self, *, task, context):
            assert task == "resume_conversation_turn_plan"
            return json.dumps({"assistant_message": "请确认范围。", "proposed_actions": [
                {"type": "update_activity_responsibility", "proposal_id": "p1"},
                {"type": "write_canonical_experience", "experience": {}},
            ], "needs_user_reply": True})

    plan = ModelGatewayConversationGateway(PlanGateway()).plan_turn(text="我独立完成", session_context={"stage": "fact_confirmation"})
    assert plan.assistant_message == "请确认范围。"
    assert plan.proposed_actions == [{"type": "update_activity_responsibility", "proposal_id": "p1"}]
    assert plan.needs_user_reply is True


def test_turn_plan_exposes_clinical_operations_as_a_supported_pack():
    recorder = RecordingGateway()

    ModelGatewayConversationGateway(recorder).plan_turn(
        text="临床项目协调", session_context={"stage": "representative_sample"}
    )

    assert "clinical_operations_v1" in recorder.calls[0][1]["allowed_role_packs"]
