import json
import pytest
from pathlib import Path

# Add src to path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.question_planner import QuestionPlannerService, ClarifyingQuestion


def test_question_planner_initialization():
    """Test that question planner initializes correctly with dimensions config."""
    planner = QuestionPlannerService()

    # Should have loaded dimensions
    assert hasattr(planner, 'dimensions')
    assert len(planner.dimensions) >= 6

    # Should have meta-analysis dimension
    assert 'meta_analysis_systematic_review' in planner.dimensions


def test_minimal_facts_question_planning():
    """Test question planning with minimal facts (should generate questions)."""
    planner = QuestionPlannerService()

    minimal_facts = {
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"]
    }

    unknown_items = ["database_count", "study_count", "screening_criteria"]
    previously_asked = []

    questions, should_stop = planner.plan_questions(
        extracted_facts=minimal_facts,
        unknown_items=unknown_items,
        previously_asked=previously_asked
    )

    # Should not stop questioning with minimal facts
    assert should_stop == False

    # Should generate some questions
    assert len(questions) > 0
    assert len(questions) <= 3

    # Questions should be ClarifyingQuestion objects
    for q in questions:
        assert isinstance(q, ClarifyingQuestion)
        assert len(q.question) > 0
        assert q.quality_gain_score > 0


def test_sufficient_facts_question_planning():
    """Test question planning with sufficient facts (should stop questioning)."""
    planner = QuestionPlannerService()

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

    questions, should_stop = planner.plan_questions(
        extracted_facts=sufficient_facts,
        unknown_items=[],
        previously_asked=[]
    )

    # Should stop questioning with sufficient facts
    assert should_stop == True
    assert len(questions) == 0


def test_question_deduplication():
    """Test that previously asked questions are not repeated."""
    planner = QuestionPlannerService()

    facts = {
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"]
    }

    unknown_items = ["database_count", "study_count"]
    previously_asked = ["Which databases did you search (PubMed, Embase, Cochrane, etc.)?"]

    questions, should_stop = planner.plan_questions(
        extracted_facts=facts,
        unknown_items=unknown_items,
        previously_asked=previously_asked
    )

    # Should not include the previously asked question
    for q in questions:
        assert q.question != previously_asked[0]


def test_role_specific_question_prioritization():
    """Test that questions are prioritized based on target roles."""
    planner = QuestionPlannerService()

    facts = {
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature", "screen_studies"],
        "methods": ["systematic_review", "meta_analysis"]
    }

    unknown_items = ["database_count", "study_count", "screening_criteria", "quality_tool", "statistical_software"]

    # Test with doctoral role (should prioritize quality assessment and statistical analysis)
    questions_doctoral, _ = planner.plan_questions(
        extracted_facts=facts,
        unknown_items=unknown_items,
        previously_asked=[],
        target_roles=["doctoral_v1"]
    )

    # Test with clinical research role (should prioritize responsibility boundary and study selection)
    questions_clinical, _ = planner.plan_questions(
        extracted_facts=facts,
        unknown_items=unknown_items,
        previously_asked=[],
        target_roles=["clinical_research_v1"]
    )

    # Both should have questions
    assert len(questions_doctoral) > 0
    assert len(questions_clinical) > 0

    # The specific questions might differ based on role priorities
    # This is a basic test - more sophisticated testing would require examining question content


def test_quality_gain_scoring():
    """Test that quality gain scoring works correctly."""
    planner = QuestionPlannerService()

    # Test base quality gain calculation
    positioning_incomplete = {
        "has_clear_identity": False,
        "has_representative_experience": True,
        "has_responsibility_boundary": False,
        "has_representative_outcomes": False,
        "information_density_score": 0.3,
        "primary_dimension": "meta_analysis_systematic_review"
    }

    base_score = planner._get_base_quality_gain("responsibility_boundary", positioning_incomplete)
    assert base_score == 1.0  # Responsibility boundary has highest base score

    # Test with complete positioning (should reduce score)
    positioning_complete = {
        "has_clear_identity": True,
        "has_representative_experience": True,
        "has_responsibility_boundary": True,
        "has_representative_outcomes": True,
        "information_density_score": 0.8,
        "primary_dimension": "meta_analysis_systematic_review"
    }

    base_score_complete = planner._get_base_quality_gain("responsibility_boundary", positioning_complete)
    assert base_score_complete < 1.0  # Should be reduced when already complete


def test_question_mapping_to_fact_categories():
    """Test that questions are correctly mapped to fact categories."""
    planner = QuestionPlannerService()

    # Test database question mapping
    db_question = "Which databases did you search?"
    category = planner._map_question_to_fact_category(db_question, 0)
    assert category == "literature_retrieval"

    # Test study count mapping
    study_question = "How many studies were included?"
    category2 = planner._map_question_to_fact_category(study_question, 1)
    assert category2 == "study_selection"

    # Test responsibility mapping
    resp_question = "What was your specific role?"
    category3 = planner._map_question_to_fact_category(resp_question, 2)
    assert category3 == "responsibility_boundary"


def test_evidence_requirement_flagging():
    """Test that questions requiring evidence are properly flagged."""
    planner = QuestionPlannerService()

    # Questions about study counts should require evidence
    study_question = ClarifyingQuestion(
        question="How many studies?",
        quality_gain_score=0.7,
        dimension="meta_analysis_systematic_review",
        fact_category="study_selection"
    )

    # Recreate the scoring process to get evidence flag
    # Provide complete positioning dict to avoid KeyError
    positioning = {
        "has_clear_identity": False,
        "has_representative_experience": False,
        "has_methodology_depth": False,
        "has_responsibility_boundary": False,
        "has_representative_outcomes": False,
        "information_density_score": 0.0,
        "primary_dimension": "meta_analysis_systematic_review"
    }

    scored_questions = planner._score_questions_by_quality_gain(
        [study_question], {}, None, positioning
    )

    assert len(scored_questions) == 1
    assert scored_questions[0].evidence_required == True

    # General questions should not require evidence
    general_question = ClarifyingQuestion(
        question="What was the background?",
        quality_gain_score=0.5,
        dimension="meta_analysis_systematic_review",
        fact_category="general_0"
    )

    scored_general = planner._score_questions_by_quality_gain(
        [general_question], {}, None, positioning
    )

    assert scored_general[0].evidence_required == False


def test_integration_with_experience_draft():
    """Test integration with ExperienceDraftService output."""
    # Import ExperienceDraftService
    from medical_career_agent.services.experience_draft import ExperienceDraftService

    draft_service = ExperienceDraftService()
    planner = QuestionPlannerService()

    # Test input similar to V3.2 sample
    experience_text = """参与急性冠脉综合征患者抗血小板治疗的Meta分析研究，在导师指导和团队协作下完成了从研究问题识别、系统检索、质量评价到结果解释的完整证据综合流程。"""

    draft = draft_service.draft(experience_text=experience_text, consent_confirmed=True)

    questions, should_stop = planner.plan_questions(
        extracted_facts=draft.extracted_facts,
        unknown_items=draft.unknown_items,
        previously_asked=[]
    )

    # Should generate questions to improve the draft
    assert len(questions) > 0
    assert len(questions) <= 3
    assert should_stop == False


if __name__ == "__main__":
    # Run tests
    test_question_planner_initialization()
    test_minimal_facts_question_planning()
    test_sufficient_facts_question_planning()
    test_question_deduplication()
    test_role_specific_question_prioritization()
    test_quality_gain_scoring()
    test_question_mapping_to_fact_categories()
    test_evidence_requirement_flagging()
    test_integration_with_experience_draft()
    print("All dynamic question planner service tests passed!")