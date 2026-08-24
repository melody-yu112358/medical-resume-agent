import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.experience_draft import ExperienceDraftService
from medical_career_agent.services.question_planner import QuestionPlannerService


def test_full_dynamic_question_workflow():
    """Test the complete dynamic question planning workflow."""
    print("Testing Dynamic Question Planner Integration")
    print("=" * 50)

    # Initialize services
    draft_service = ExperienceDraftService()
    planner = QuestionPlannerService()

    # Test case 1: Minimal input
    print("\nTest 1: Minimal Meta-analysis input")
    experience_text = "参与Meta分析研究"

    draft = draft_service.draft(experience_text=experience_text, consent_confirmed=True)
    print(f"Extracted facts: {len(draft.extracted_facts)} fields")
    print(f"Unknown items: {len(draft.unknown_items)}")
    print(f"Questions generated: {len(draft.clarifying_questions)}")
    for i, q in enumerate(draft.clarifying_questions, 1):
        print(f"  {i}. {q}")

    # Test case 2: Rich input (similar to V3.2)
    print("\nTest 2: Rich Meta-analysis input (V3.2 style)")
    rich_experience = """参与急性冠脉综合征患者抗血小板治疗的Meta分析研究，在导师指导和团队协作下完成了从研究问题识别、系统检索、质量评价到结果解释的完整证据综合流程。"""

    rich_draft = draft_service.draft(experience_text=rich_experience, consent_confirmed=True)
    print(f"Extracted facts: {len(rich_draft.extracted_facts)} fields")
    print(f"Unknown items: {len(rich_draft.unknown_items)}")
    print(f"Questions generated: {len(rich_draft.clarifying_questions)}")
    for i, q in enumerate(rich_draft.clarifying_questions, 1):
        print(f"  {i}. {q}")

    # Test case 3: Simulate multi-round questioning
    print("\nTest 3: Multi-round questioning simulation")
    initial_draft = draft_service.draft(experience_text="做Meta分析", consent_confirmed=True)
    round1_questions = initial_draft.clarifying_questions
    print(f"Round 1 questions: {len(round1_questions)}")

    # Simulate answering first question about databases
    updated_facts = initial_draft.extracted_facts.copy()
    updated_facts["tools"] = ["pubmed", "embase", "cochrane"]
    updated_facts["scope"] = {"database_count": "3"}

    # Plan next round of questions
    round2_questions, should_stop = planner.plan_questions(
        extracted_facts=updated_facts,
        unknown_items=["study_count", "screening_criteria", "quality_tool"],
        previously_asked=round1_questions
    )
    print(f"Round 2 questions: {len(round2_questions)}")
    print(f"Should stop questioning: {should_stop}")
    for i, q in enumerate(round2_questions, 1):
        print(f"  {i}. {q.question}")

    # Test case 4: Sufficient information stops questioning
    print("\nTest 4: Sufficient information test")
    sufficient_facts = {
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "Cardiovascular meta-analysis"},
        "role": {"responsibility_level": "participated", "personal_boundary": "Participated in literature retrieval under supervision"},
        "background": "Clinical uncertainty about antiplatelet therapy in ACS",
        "problem_or_goal": "Compare efficacy of different antiplatelet drugs",
        "actions": ["retrieve_literature", "screen_studies", "extract_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["pubmed", "embase", "cochrane", "spss", "r"],
        "objects": ["medical_literature", "clinical_studies"],
        "collaboration": ["research_team", "supervisor"],
        "artifacts": ["prisma_flowchart", "data_extraction_sheet"],
        "outcomes": ["Third author on submitted manuscript"],
        "scope": {"database_count": "3", "study_count": "45"}
    }

    final_questions, should_stop_final = planner.plan_questions(
        extracted_facts=sufficient_facts,
        unknown_items=[],
        previously_asked=[]
    )
    print(f"Final questions: {len(final_questions)}")
    print(f"Should stop questioning: {should_stop_final}")

    print("\n" + "=" * 50)
    print("Dynamic Question Planner Integration Test Complete!")
if __name__ == "__main__":
    test_full_dynamic_question_workflow()
    print("\nAll tests passed!")
