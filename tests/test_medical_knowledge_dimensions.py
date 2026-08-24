import json
import pytest
from pathlib import Path

# Add src to path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_medical_knowledge_dimensions_schema():
    """Test that medical knowledge dimensions configuration loads and validates correctly."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    # Should have medical_knowledge_dimensions root key
    assert "medical_knowledge_dimensions" in dimensions_config

    dimensions = dimensions_config["medical_knowledge_dimensions"]

    # Should have all expected dimensions
    expected_dimensions = [
        "meta_analysis_systematic_review",
        "clinical_research",
        "wet_lab_research",
        "data_analysis_medical",
        "medical_writing_literature",
        "clinical_practice"
    ]

    for dim_name in expected_dimensions:
        assert dim_name in dimensions, f"Missing dimension: {dim_name}"

    # Test meta-analysis dimension structure
    meta_dim = dimensions["meta_analysis_systematic_review"]
    assert "name" in meta_dim
    assert "description" in meta_dim
    assert "identifiable_expressions" in meta_dim
    assert "required_hard_facts" in meta_dim
    assert "professional_context" in meta_dim
    assert "role_specific_value" in meta_dim
    assert "high_risk_content" in meta_dim
    assert "recommended_questions" in meta_dim

    # Test role-specific value has all four roles
    role_values = meta_dim["role_specific_value"]
    expected_roles = ["doctoral_v1", "clinical_research_v1", "medical_affairs_v1", "health_ai_data_v1"]
    for role in expected_roles:
        assert role in role_values, f"Missing role {role} in meta-analysis dimension"


def test_dimension_identifiable_expressions():
    """Test that identifiable expressions are properly configured."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    dimensions = dimensions_config["medical_knowledge_dimensions"]

    # Test meta-analysis expressions include both Chinese and English terms
    meta_expressions = dimensions["meta_analysis_systematic_review"]["identifiable_expressions"]
    assert "Meta分析" in meta_expressions
    assert "systematic review" in meta_expressions
    assert "PRISMA" in meta_expressions

    # Test clinical research expressions
    clinical_expressions = dimensions["clinical_research"]["identifiable_expressions"]
    assert "临床研究" in clinical_expressions
    assert "clinical trial" in clinical_expressions
    assert "IRB" in clinical_expressions


def test_required_hard_facts_structure():
    """Test that required hard facts have proper structure."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    dimensions = dimensions_config["medical_knowledge_dimensions"]

    # Test meta-analysis required facts
    meta_facts = dimensions["meta_analysis_systematic_review"]["required_hard_facts"]
    assert "context" in meta_facts
    assert "role" in meta_facts
    assert "actions" in meta_facts
    assert "methods" in meta_facts
    assert "scope" in meta_facts

    # Test that actions include expected values
    assert "retrieve_literature" in meta_facts["actions"]
    assert "screen_studies" in meta_facts["actions"]
    assert "extract_data" in meta_facts["actions"]


def test_professional_context_completeness():
    """Test that professional context includes all expected fields."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    dimensions = dimensions_config["medical_knowledge_dimensions"]

    meta_context = dimensions["meta_analysis_systematic_review"]["professional_context"]
    assert "background" in meta_context
    assert "problem_or_goal" in meta_context
    assert "workflow_steps" in meta_context
    assert "quality_control" in meta_context

    # Test workflow steps have reasonable content
    assert len(meta_context["workflow_steps"]) >= 5
    assert "Research question formulation" in meta_context["workflow_steps"][0]


def test_role_specific_value_differentiation():
    """Test that role-specific values are meaningfully different across roles."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    dimensions = dimensions_config["medical_knowledge_dimensions"]
    meta_values = dimensions["meta_analysis_systematic_review"]["role_specific_value"]

    # Doctoral should emphasize research methodology and academic contribution
    doctoral_values = meta_values["doctoral_v1"]
    assert "methodology" in doctoral_values
    assert "academic_contribution" in doctoral_values

    # Clinical research should emphasize protocol execution and data quality
    clinical_values = meta_values["clinical_research_v1"]
    assert "protocol_execution" in clinical_values
    assert "data_quality" in clinical_values

    # Medical affairs should emphasize evidence synthesis and communication
    medical_affairs_values = meta_values["medical_affairs_v1"]
    assert "evidence_synthesis" in medical_affairs_values
    assert "scientific_communication" in medical_affairs_values

    # Health AI should emphasize data curation and systematic approaches
    health_ai_values = meta_values["health_ai_data_v1"]
    assert "data_curation" in health_ai_values
    assert "systematic_approach" in health_ai_values


def test_high_risk_content_configuration():
    """Test that high-risk content restrictions are properly configured."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    dimensions = dimensions_config["medical_knowledge_dimensions"]

    meta_risk = dimensions["meta_analysis_systematic_review"]["high_risk_content"]
    assert "forbidden_claims" in meta_risk
    assert "restricted_verbs" in meta_risk
    assert "unverifiable_outcomes" in meta_risk

    # Test forbidden claims include responsibility upgrades
    forbidden_claims = meta_risk["forbidden_claims"]
    assert "independently conducted meta-analysis" in forbidden_claims
    assert "led systematic review" in forbidden_claims

    # Test restricted verbs include strong action words
    restricted_verbs = meta_risk["restricted_verbs"]
    assert "independently" in restricted_verbs
    assert "led" in restricted_verbs


def test_recommended_questions_appropriateness():
    """Test that recommended questions are appropriate and specific."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    dimensions = dimensions_config["medical_knowledge_dimensions"]

    meta_questions = dimensions["meta_analysis_systematic_review"]["recommended_questions"]
    assert len(meta_questions) >= 5
    assert len(meta_questions) <= 7  # Reasonable number of questions

    # Questions should be specific and answerable
    assert "Which databases did you search" in meta_questions[0]
    assert "How many studies were included" in meta_questions[1]
    assert "What inclusion/exclusion criteria" in meta_questions[2]


def test_all_dimensions_have_consistent_structure():
    """Test that all dimensions follow the same structural pattern."""
    dimensions_path = Path(__file__).parent.parent / "data" / "medical-knowledge-dimensions.json"

    with open(dimensions_path, 'r', encoding='utf-8') as f:
        dimensions_config = json.load(f)

    dimensions = dimensions_config["medical_knowledge_dimensions"]

    expected_fields = [
        "name", "description", "identifiable_expressions", "required_hard_facts",
        "professional_context", "role_specific_value", "high_risk_content", "recommended_questions"
    ]

    for dim_name, dim_config in dimensions.items():
        for field in expected_fields:
            assert field in dim_config, f"Dimension {dim_name} missing field {field}"


if __name__ == "__main__":
    # Run tests
    test_medical_knowledge_dimensions_schema()
    test_dimension_identifiable_expressions()
    test_required_hard_facts_structure()
    test_professional_context_completeness()
    test_role_specific_value_differentiation()
    test_high_risk_content_configuration()
    test_recommended_questions_appropriateness()
    test_all_dimensions_have_consistent_structure()
    print("All medical knowledge dimensions configuration tests passed!")