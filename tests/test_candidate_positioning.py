import json
import pytest
from pathlib import Path

# Add src to path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.candidate_positioning import CandidatePositioningService, CandidatePositioning


def test_candidate_positioning_initialization():
    """Test that candidate positioning service initializes correctly."""
    service = CandidatePositioningService()
    assert hasattr(service, 'dimensions')
    assert len(service.dimensions) >= 6


def test_basic_positioning_generation():
    """Test basic positioning generation with minimal experience."""
    service = CandidatePositioningService()

    minimal_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[minimal_experience],
        target_roles=["doctoral_v1"]
    )

    # Should have all required fields
    assert isinstance(positioning, CandidatePositioning)
    assert len(positioning.identity) > 0
    assert len(positioning.core_capabilities) > 0
    assert len(positioning.representative_experience) > 0
    assert len(positioning.experience_mainline) > 0
    assert len(positioning.differentiation) > 0
    assert isinstance(positioning.current_weaknesses, list)
    assert isinstance(positioning.worth_supplementing_facts, list)
    assert isinstance(positioning.suggested_section_order, list)
    assert isinstance(positioning.resume_appropriate_content, list)
    assert isinstance(positioning.interview_only_content, list)
    assert len(positioning.evidence_ids) > 0


def test_doctoral_positioning():
    """Test positioning for doctoral applications."""
    service = CandidatePositioningService()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "meta_analysis_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "Cardiovascular meta-analysis"},
        "role": {"responsibility_level": "participated"},
        "background": "Clinical uncertainty about antiplatelet therapy",
        "problem_or_goal": "Compare efficacy of different antiplatelet drugs",
        "actions": ["retrieve_literature", "screen_studies", "extract_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["r", "spss"],
        "outcomes": ["Third author on submitted manuscript"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[experience],
        target_roles=["doctoral_v1"]
    )

    # Should have doctoral-specific identity
    assert "Evidence synthesis researcher" in positioning.identity

    # Should prioritize research experience in section order
    assert positioning.suggested_section_order[0] == "Research Experience"

    # Should have research-focused capabilities
    assert any("Systematic review" in cap or "Meta-analysis" in cap for cap in positioning.core_capabilities)


def test_clinical_research_positioning():
    """Test positioning for clinical research roles."""
    service = CandidatePositioningService()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "clinical_trial_001",
        "evidence_ids": ["ev_002"],
        "context": {"domain": "clinical_research", "setting": "clinical_trial", "topic": "Patient recruitment study"},
        "role": {"responsibility_level": "participated"},
        "actions": ["collect_data", "screen_patients"],
        "methods": ["cohort_study"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[experience],
        target_roles=["clinical_research_v1"]
    )

    # Should have clinical research identity
    assert "Clinical research specialist" in positioning.identity

    # Should prioritize clinical experience in section order
    assert positioning.suggested_section_order[0] == "Clinical Experience"


def test_medical_affairs_positioning():
    """Test positioning for medical affairs roles."""
    service = CandidatePositioningService()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "literature_review_001",
        "evidence_ids": ["ev_003"],
        "context": {"domain": "medical_information", "setting": "literature_work", "topic": "Therapeutic area review"},
        "role": {"responsibility_level": "participated"},
        "actions": ["review_literature", "write_manuscript"],
        "methods": ["narrative_review"],
        "outcomes": ["Published review article"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[experience],
        target_roles=["medical_affairs_v1"]
    )

    # Should have medical affairs identity
    assert "Medical evidence communicator" in positioning.identity

    # Should prioritize publications in section order
    assert positioning.suggested_section_order[1] == "Publications"


def test_health_ai_data_positioning():
    """Test positioning for health AI/data roles."""
    service = CandidatePositioningService()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "data_analysis_001",
        "evidence_ids": ["ev_004"],
        "context": {"domain": "data_analysis", "setting": "data_project", "topic": "Predictive modeling study"},
        "role": {"responsibility_level": "participated"},
        "actions": ["analyze_data", "create_visualizations"],
        "methods": ["regression_modeling", "machine_learning"],
        "tools": ["python", "r", "tableau"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[experience],
        target_roles=["health_ai_data_v1"]
    )

    # Should have data specialist identity
    assert "Healthcare data specialist" in positioning.identity

    # Should prioritize skills in section order
    assert positioning.suggested_section_order[0] == "Skills"


def test_multiple_experiences_positioning():
    """Test positioning with multiple experiences."""
    service = CandidatePositioningService()

    experiences = [
        {
            "schema_version": "canonical-experience-v1",
            "experience_id": "meta_analysis_001",
            "evidence_ids": ["ev_001"],
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "role": {"responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review"],
            "status": "user_confirmed"
        },
        {
            "schema_version": "canonical-experience-v1",
            "experience_id": "wet_lab_001",
            "evidence_ids": ["ev_002"],
            "context": {"domain": "wet_lab", "setting": "lab_experiment"},
            "role": {"responsibility_level": "participated"},
            "actions": ["perform_experiments"],
            "methods": ["cell_culture"],
            "status": "user_confirmed"
        }
    ]

    positioning = service.generate_positioning(
        canonical_experiences=experiences,
        target_roles=["doctoral_v1"]
    )

    # Should have integrated mainline
    assert "multiple domains" in positioning.experience_mainline or "Integrated" in positioning.experience_mainline

    # Should have more capabilities
    assert len(positioning.core_capabilities) >= 4


def test_differentiation_generation():
    """Test differentiation generation based on experience quality."""
    service = CandidatePositioningService()

    # Comprehensive experience
    comprehensive_exp = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "comprehensive_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "Comprehensive study"},
        "role": {"responsibility_level": "participated"},
        "background": "Background info",
        "problem_or_goal": "Clear problem statement",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["r", "spss"],
        "workflow_steps": ["Step 1", "Step 2"],
        "quality_control": ["QC measure"],
        "collaboration": ["team"],
        "artifacts": ["artifact"],
        "outcomes": ["outcome"],
        "scope": {"count": "10"},
        "status": "user_confirmed"
    }

    # Minimal experience
    minimal_exp = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "minimal_001",
        "evidence_ids": ["ev_002"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "status": "user_confirmed"
    }

    # Test comprehensive differentiation
    positioning_comp = service.generate_positioning(
        canonical_experiences=[comprehensive_exp],
        target_roles=["doctoral_v1"]
    )
    assert "Deep expertise" in positioning_comp.differentiation

    # Test minimal differentiation
    positioning_min = service.generate_positioning(
        canonical_experiences=[minimal_exp],
        target_roles=["doctoral_v1"]
    )
    assert "Strong foundation" in positioning_min.differentiation


def test_weaknesses_identification():
    """Test identification of current weaknesses."""
    service = CandidatePositioningService()

    # Experience without outcomes
    no_outcomes_exp = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "no_outcomes_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[no_outcomes_exp],
        target_roles=["doctoral_v1"]
    )

    # Should identify missing outcomes as weakness
    assert any("outcomes" in weakness.lower() for weakness in positioning.current_weaknesses)


def test_supplemental_facts_identification():
    """Test identification of facts worth supplementing."""
    service = CandidatePositioningService()

    minimal_exp = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "minimal_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[minimal_exp],
        target_roles=["doctoral_v1"]
    )

    # Should suggest adding outcomes and scope details
    supplemental_text = " ".join(positioning.worth_supplementing_facts).lower()
    assert "outcomes" in supplemental_text or "scope" in supplemental_text


def test_to_dict_conversion():
    """Test conversion to dictionary format."""
    service = CandidatePositioningService()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"],
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[experience],
        target_roles=["doctoral_v1"]
    )

    positioning_dict = positioning.to_dict()

    # Should have all expected keys
    expected_keys = [
        "identity", "core_capabilities", "representative_experience", "experience_mainline",
        "differentiation", "current_weaknesses", "worth_supplementing_facts",
        "suggested_section_order", "resume_appropriate_content", "interview_only_content",
        "evidence_ids"
    ]

    for key in expected_keys:
        assert key in positioning_dict


if __name__ == "__main__":
    # Run tests
    test_candidate_positioning_initialization()
    test_basic_positioning_generation()
    test_doctoral_positioning()
    test_clinical_research_positioning()
    test_medical_affairs_positioning()
    test_health_ai_data_positioning()
    test_multiple_experiences_positioning()
    test_differentiation_generation()
    test_weaknesses_identification()
    test_supplemental_facts_identification()
    test_to_dict_conversion()
    print("All candidate positioning service tests passed!")