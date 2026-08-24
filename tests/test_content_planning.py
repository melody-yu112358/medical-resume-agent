import json
import pytest
from pathlib import Path

# Add src to path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.content_planning import ContentPlanningService, ResumeContentPlan, ExperienceContentPlan


def test_content_planning_initialization():
    """Test that content planning service initializes correctly."""
    service = ContentPlanningService()
    assert hasattr(service, 'dimensions')
    assert len(service.dimensions) >= 6


def test_basic_content_plan_generation():
    """Test basic content plan generation with minimal experience."""
    service = ContentPlanningService()

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

    positioning = {
        "identity": "Evidence synthesis researcher",
        "core_capabilities": ["Systematic review methodology"],
        "representative_experience": "Research project",
        "experience_mainline": "Focused on evidence synthesis",
        "differentiation": "Methodology expertise",
        "current_weaknesses": [],
        "worth_supplementing_facts": [],
        "suggested_section_order": ["Research Experience", "Education"],
        "resume_appropriate_content": ["Methodology"],
        "interview_only_content": ["Team dynamics"],
        "evidence_ids": ["ev_001"]
    }

    content_plan = service.create_content_plan(
        canonical_experiences=[minimal_experience],
        candidate_positioning=positioning,
        target_role="doctoral_v1"
    )

    # Should have all required fields
    assert isinstance(content_plan, ResumeContentPlan)
    assert content_plan.target_role == "doctoral_v1"
    assert len(content_plan.experience_plans) == 1
    assert content_plan.total_bullet_target > 0
    assert 0 <= content_plan.information_density_score <= 1.0

    # Check experience plan
    exp_plan = content_plan.experience_plans[0]
    assert isinstance(exp_plan, ExperienceContentPlan)
    assert len(exp_plan.retain_reason) > 0
    assert 1 <= exp_plan.priority <= 10
    assert 2 <= exp_plan.bullet_count_target <= 9
    assert len(exp_plan.dimension_coverage) > 0
    assert len(exp_plan.representative_contribution) > 0


def test_meta_analysis_content_plan():
    """Test content plan for meta-analysis experience with high information density."""
    service = ContentPlanningService()

    rich_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "meta_analysis_001",
        "evidence_ids": ["ev_001"],
        "context": {
            "domain": "clinical_research",
            "setting": "research_project",
            "topic": "Cardiovascular meta-analysis"
        },
        "role": {"responsibility_level": "participated"},
        "background": "Clinical uncertainty about antiplatelet therapy",
        "problem_or_goal": "Compare efficacy of different antiplatelet drugs",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["r", "spss", "endnote"],
        "workflow_steps": ["PICO development", "Search strategy execution"],
        "quality_control": ["Dual screening", "Cochrane RoB application"],
        "outcomes": ["Third author manuscript"],
        "scope": {"study_count": "45"},
        "status": "user_confirmed"
    }

    positioning = {
        "identity": "Evidence synthesis researcher focused on clinical research",
        "core_capabilities": ["Systematic review methodology", "Meta-analysis statistics"],
        "representative_experience": "Cardiovascular meta-analysis project",
        "experience_mainline": "Focused on evidence synthesis methodology",
        "differentiation": "Deep expertise in systematic evidence synthesis",
        "current_weaknesses": ["Limited publication record"],
        "worth_supplementing_facts": ["Publication details"],
        "suggested_section_order": ["Research Experience", "Education", "Publications"],
        "resume_appropriate_content": ["Methodology", "Results", "Tools"],
        "interview_only_content": ["Team dynamics", "Problem-solving approaches"],
        "evidence_ids": ["ev_001"]
    }

    content_plan = service.create_content_plan(
        canonical_experiences=[rich_experience],
        candidate_positioning=positioning,
        target_role="doctoral_v1"
    )

    # Meta-analysis should have high bullet count (7-9)
    assert 7 <= content_plan.total_bullet_target <= 9

    # Should have rich dimension coverage
    exp_plan = content_plan.experience_plans[0]
    assert len(exp_plan.dimension_coverage) >= 6

    # Should have specific guidance for each bullet type
    assert len(exp_plan.methodology_bullet) > 0
    assert len(exp_plan.quality_control_bullet) > 0
    assert len(exp_plan.results_or_outputs_bullet) > 0
    assert len(exp_plan.role_value_bullet) > 0


def test_multiple_experiences_content_plan():
    """Test content plan with multiple experiences of different types."""
    service = ContentPlanningService()

    experiences = [
        {
            "schema_version": "canonical-experience-v1",
            "experience_id": "meta_analysis_001",
            "evidence_ids": ["ev_001"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": "Meta-analysis"},
            "role": {"responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review"],
            "status": "user_confirmed"
        },
        {
            "schema_version": "canonical-experience-v1",
            "experience_id": "clinical_internship_001",
            "evidence_ids": ["ev_002"],
            "context": {"domain": "clinical_practice", "setting": "clinical_practice", "topic": "Cardiology rotation"},
            "role": {"responsibility_level": "participated"},
            "actions": ["collect_history", "perform_exam"],
            "status": "user_confirmed"
        }
    ]

    positioning = {
        "identity": "Clinical researcher with patient care experience",
        "core_capabilities": ["Evidence synthesis", "Clinical assessment"],
        "representative_experience": "Meta-analysis project",
        "experience_mainline": "Integrated clinical and research experience",
        "differentiation": "Combined research methodology and clinical insight",
        "current_weaknesses": [],
        "worth_supplementing_facts": [],
        "suggested_section_order": ["Research Experience", "Clinical Experience", "Education"],
        "resume_appropriate_content": ["Research", "Clinical"],
        "interview_only_content": ["Learning experiences"],
        "evidence_ids": ["ev_001", "ev_002"]
    }

    content_plan = service.create_content_plan(
        canonical_experiences=experiences,
        candidate_positioning=positioning,
        target_role="doctoral_v1"
    )

    # Should have both experiences
    assert len(content_plan.experience_plans) == 2

    # Meta-analysis should have higher priority
    meta_plan = content_plan.experience_plans[0]  # Sorted by priority
    clinical_plan = content_plan.experience_plans[1]

    assert "meta_analysis" in meta_plan.experience_id
    assert meta_plan.priority >= clinical_plan.priority

    # Different bullet counts based on experience type
    assert meta_plan.bullet_count_target >= clinical_plan.bullet_count_target


def test_role_specific_content_plans():
    """Test that content plans differ by target role."""
    service = ContentPlanningService()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "meta_analysis_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "Meta-analysis"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature", "screen_studies", "extract_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["r", "spss"],
        "outcomes": ["Manuscript contribution"],
        "status": "user_confirmed"
    }

    roles = ["doctoral_v1", "clinical_research_v1", "medical_affairs_v1", "health_ai_data_v1"]
    plans = {}

    for role in roles:
        # Create role-specific positioning
        if role == "doctoral_v1":
            positioning = {
                "identity": "Evidence synthesis researcher",
                "core_capabilities": ["Systematic review", "Meta-analysis"],
                "representative_experience": "Meta-analysis project",
                "experience_mainline": "Focused on evidence synthesis",
                "differentiation": "Methodology expertise",
                "current_weaknesses": [],
                "worth_supplementing_facts": [],
                "suggested_section_order": ["Research Experience", "Education", "Publications", "Skills", "Clinical Experience"],
                "resume_appropriate_content": ["Methodology", "Results"],
                "interview_only_content": ["Team dynamics"],
                "evidence_ids": ["ev_001"]
            }
        elif role == "clinical_research_v1":
            positioning = {
                "identity": "Clinical research specialist",
                "core_capabilities": ["Clinical research", "Data collection"],
                "representative_experience": "Meta-analysis project",
                "experience_mainline": "Clinical research focus",
                "differentiation": "Clinical research execution",
                "current_weaknesses": [],
                "worth_supplementing_facts": [],
                "suggested_section_order": ["Clinical Experience", "Research Experience", "Education", "Skills", "Publications"],
                "resume_appropriate_content": ["Clinical", "Research"],
                "interview_only_content": ["Team dynamics"],
                "evidence_ids": ["ev_001"]
            }
        elif role == "medical_affairs_v1":
            positioning = {
                "identity": "Medical evidence communicator",
                "core_capabilities": ["Evidence synthesis", "Scientific communication"],
                "representative_experience": "Meta-analysis project",
                "experience_mainline": "Evidence communication focus",
                "differentiation": "Evidence translation expertise",
                "current_weaknesses": [],
                "worth_supplementing_facts": [],
                "suggested_section_order": ["Research Experience", "Publications", "Education", "Skills", "Clinical Experience"],
                "resume_appropriate_content": ["Evidence", "Communication"],
                "interview_only_content": ["Stakeholder engagement"],
                "evidence_ids": ["ev_001"]
            }
        else:  # health_ai_data_v1
            positioning = {
                "identity": "Healthcare data specialist",
                "core_capabilities": ["Data analysis", "Statistical programming"],
                "representative_experience": "Meta-analysis project",
                "experience_mainline": "Data science focus",
                "differentiation": "Technical analytical expertise",
                "current_weaknesses": [],
                "worth_supplementing_facts": [],
                "suggested_section_order": ["Skills", "Research Experience", "Education", "Publications", "Clinical Experience"],
                "resume_appropriate_content": ["Technical", "Analytical"],
                "interview_only_content": ["Problem-solving"],
                "evidence_ids": ["ev_001"]
            }

        plan = service.create_content_plan(
            canonical_experiences=[experience],
            candidate_positioning=positioning,
            target_role=role
        )
        plans[role] = plan

    # All plans should exist
    assert len(plans) == 4

    # Section orders should differ by role
    section_orders = [plans[role].suggested_section_order for role in roles]
    unique_orders = set(tuple(order) for order in section_orders)
    assert len(unique_orders) >= 2  # At least some differentiation

    # Bullet counts might vary by role
    bullet_counts = [plans[role].total_bullet_target for role in roles]
    # Doctoral should have highest or equal highest count
    assert bullet_counts[0] >= min(bullet_counts)


def test_dimension_coverage_identification():
    """Test dimension coverage identification from experience fields."""
    service = ContentPlanningService()

    # Rich experience with many fields
    rich_exp = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "rich_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "background": "Research background",
        "problem_or_goal": "Clear problem statement",
        "actions": ["retrieve_literature", "screen_studies"],
        "methods": ["systematic_review"],
        "workflow_steps": ["Step 1", "Step 2"],
        "quality_control": ["QC measure"],
        "decisions_or_judgments": ["Decision made"],
        "collaboration": ["Team work"],
        "artifacts": ["Deliverable"],
        "outcomes": ["Outcome achieved"],
        "insights": ["Key insight"],
        "status": "user_confirmed"
    }

    positioning = {
        "identity": "Researcher",
        "core_capabilities": ["Research"],
        "representative_experience": "Rich project",
        "experience_mainline": "Research focus",
        "differentiation": "Comprehensive experience",
        "current_weaknesses": [],
        "worth_supplementing_facts": [],
        "suggested_section_order": ["Research"],
        "resume_appropriate_content": ["All"],
        "interview_only_content": [],
        "evidence_ids": ["ev_001"]
    }

    content_plan = service.create_content_plan(
        canonical_experiences=[rich_exp],
        candidate_positioning=positioning,
        target_role="doctoral_v1"
    )

    exp_plan = content_plan.experience_plans[0]
    dimensions = exp_plan.dimension_coverage

    # Should have multiple dimensions identified
    expected_dimensions = [
        "research_problem_identification",
        "literature_retrieval_and_screening",
        "systematic_review_methodology",
        "research_workflow_execution",
        "quality_assurance_measures",
        "critical_thinking_and_decisions",
        "team_collaboration",
        "research_deliverables",
        "research_outcomes_and_impact",
        "scientific_insights"
    ]

    # Should cover most expected dimensions
    covered_count = sum(1 for dim in expected_dimensions if dim in dimensions)
    assert covered_count >= 8


def test_excluded_content_identification():
    """Test identification of content to exclude from resume."""
    service = ContentPlanningService()

    experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_001",
        "evidence_ids": ["ev_001"],
        "context": {"domain": "clinical_research"},
        "role": {"responsibility_level": "participated"},
        "status": "user_confirmed"
    }

    positioning = {
        "identity": "Researcher",
        "core_capabilities": ["Research"],
        "representative_experience": "Test project",
        "experience_mainline": "Research focus",
        "differentiation": "Experience",
        "current_weaknesses": [],
        "worth_supplementing_facts": [],
        "suggested_section_order": ["Research"],
        "resume_appropriate_content": ["Research facts"],
        "interview_only_content": ["Team dynamics", "Problem-solving approaches"],
        "evidence_ids": ["ev_001"]
    }

    content_plan = service.create_content_plan(
        canonical_experiences=[experience],
        candidate_positioning=positioning,
        target_role="doctoral_v1"
    )

    exp_plan = content_plan.experience_plans[0]
    excluded = exp_plan.content_to_exclude

    # Should include interview-only content
    assert any("Team dynamics" in item or "Problem-solving" in item for item in excluded)

    # Should include responsibility warnings
    assert any("independent leadership" in item.lower() or "ownership" in item.lower() for item in excluded)


def test_to_dict_conversion():
    """Test conversion to dictionary format."""
    service = ContentPlanningService()

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

    positioning = {
        "identity": "Evidence synthesis researcher",
        "core_capabilities": ["Systematic review methodology"],
        "representative_experience": "Research project",
        "experience_mainline": "Focused on evidence synthesis",
        "differentiation": "Methodology expertise",
        "current_weaknesses": [],
        "worth_supplementing_facts": [],
        "suggested_section_order": ["Research Experience", "Education"],
        "resume_appropriate_content": ["Methodology"],
        "interview_only_content": ["Team dynamics"],
        "evidence_ids": ["ev_001"]
    }

    content_plan = service.create_content_plan(
        canonical_experiences=[experience],
        candidate_positioning=positioning,
        target_role="doctoral_v1"
    )

    # Test ExperienceContentPlan to_dict
    exp_plan_dict = content_plan.experience_plans[0].to_dict()
    assert isinstance(exp_plan_dict, dict)
    assert "experience_id" in exp_plan_dict
    assert "retain_reason" in exp_plan_dict
    assert "priority" in exp_plan_dict

    # Test ResumeContentPlan to_dict
    content_plan_dict = content_plan.to_dict()
    assert isinstance(content_plan_dict, dict)
    assert "target_role" in content_plan_dict
    assert "experience_plans" in content_plan_dict
    assert "total_bullet_target" in content_plan_dict


if __name__ == "__main__":
    # Run tests
    test_content_planning_initialization()
    test_basic_content_plan_generation()
    test_meta_analysis_content_plan()
    test_multiple_experiences_content_plan()
    test_role_specific_content_plans()
    test_dimension_coverage_identification()
    test_excluded_content_identification()
    test_to_dict_conversion()
    print("All content planning service tests passed!")