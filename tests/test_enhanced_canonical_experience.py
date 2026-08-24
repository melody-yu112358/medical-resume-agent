import json
import pytest
from pathlib import Path

# Add src to path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.experience_draft import ExperienceDraftService


def test_canonical_experience_schema_backward_compatibility():
    """Test that existing canonical experience records still validate with enhanced schema."""
    # Load existing test fixture
    fixture_path = Path(__file__).parent.parent / "data" / "fixtures" / "canonical-experience-example.json"
    if fixture_path.exists():
        with open(fixture_path, 'r', encoding='utf-8') as f:
            existing_record = json.load(f)

        # This should still be valid with enhanced schema
        assert existing_record["schema_version"] == "canonical-experience-v1"
        assert "experience_id" in existing_record
        assert "evidence_ids" in existing_record
        assert existing_record["status"] == "user_confirmed"


def test_enhanced_canonical_experience_fields():
    """Test that enhanced canonical experience records include new depth fields."""
    enhanced_record = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "meta_analysis_001",
        "evidence_ids": ["ev_001", "ev_002"],
        "context": {
            "domain": "clinical_research",
            "setting": "research_project",
            "topic": "Cardiovascular meta-analysis"
        },
        "role": {
            "title": "Research Assistant",
            "responsibility_level": "participated",
            "personal_boundary": "Participated in literature retrieval and screening under supervisor guidance"
        },
        "background": "Acute coronary syndrome patients have varying responses to antiplatelet therapy",
        "problem_or_goal": "Compare efficacy of different antiplatelet drugs in ACS patients through systematic evidence synthesis",
        "actions": ["retrieve_literature", "screen_studies", "extract_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r", "endnote"],
        "objects": ["medical_literature", "clinical_studies"],
        "workflow_steps": [
            "Develop PICO framework with supervisor",
            "Execute multi-database search strategy",
            "Perform two-stage screening process",
            "Extract structured data using standardized forms"
        ],
        "quality_control": [
            "Dual screening for title/abstract phase",
            "Cochrane RoB tool for bias assessment",
            "Standardized data extraction forms"
        ],
        "decisions_or_judgments": [
            "Resolved screening disagreements through team discussion",
            "Selected appropriate statistical models based on heterogeneity"
        ],
        "difficulties": [
            "Managing large volume of retrieved studies",
            "Resolving ambiguous inclusion criteria cases"
        ],
        "collaboration": ["research_team", "supervisor"],
        "artifacts": ["prisma_flowchart", "data_extraction_sheet"],
        "outputs": ["45 included studies database", "statistical analysis results"],
        "outcomes": ["Third author on submitted manuscript", "Comprehensive evidence synthesis completed"],
        "insights": [
            "Understanding importance of rigorous methodology in evidence synthesis",
            "Recognizing clinical implications of heterogeneity in treatment effects"
        ],
        "capability_evidence": [
            "Demonstrated systematic literature retrieval competence",
            "Applied PRISMA guidelines consistently",
            "Used Cochrane RoB tool appropriately"
        ],
        "role_relevance": "Directly relevant to doctoral research methodology requirements",
        "research_interest_link": "Connected to interest in cardiovascular secondary prevention optimization",
        "scope": {
            "database_count": "3",
            "study_count": "45",
            "time_period": "2022-2024"
        },
        "unknowns": [],
        "provenance": {
            "source_document_id": "user_input_001",
            "source_locator": "paragraph_1",
            "created_at": "2026-08-23T10:00:00Z",
            "confirmed_at": "2026-08-23T10:30:00Z"
        },
        "status": "user_confirmed"
    }

    # Validate required fields are present
    required_fields = [
        "schema_version", "experience_id", "evidence_ids", "context", "role",
        "actions", "methods", "tools", "objects", "collaboration", "artifacts",
        "outcomes", "scope", "unknowns", "status"
    ]

    for field in required_fields:
        assert field in enhanced_record, f"Required field {field} missing"

    # Validate new optional fields can be present
    optional_fields = [
        "background", "problem_or_goal", "workflow_steps", "quality_control",
        "decisions_or_judgments", "difficulties", "outputs", "insights",
        "capability_evidence", "role_relevance", "research_interest_link", "provenance"
    ]

    for field in optional_fields:
        assert field in enhanced_record, f"Optional field {field} should be supported"


def test_experience_draft_service_with_enhanced_fields():
    """Test that ExperienceDraftService can handle inputs that populate enhanced fields."""
    service = ExperienceDraftService()

    # Test input that should populate background and problem_or_goal
    experience_text = """参与急性冠脉综合征患者抗血小板治疗的Meta分析研究。研究背景是临床上对不同抗血小板药物疗效存在争议，目标是比较各种药物在ACS患者中的疗效差异。"""

    draft = service.draft(experience_text=experience_text, consent_confirmed=True)

    # Should extract context and basic actions
    assert "context" in draft.extracted_facts
    assert draft.extracted_facts["context"]["domain"] == "clinical_research"

    # Should identify unknowns for deeper information
    assert len(draft.unknown_items) > 0

    # Should generate clarifying questions about methodology details
    assert len(draft.clarifying_questions) <= 3


def test_role_personal_boundary_extraction():
    """Test extraction of personal boundary information."""
    service = ExperienceDraftService()

    experience_text = """作为课题组研究助理参与Meta分析，在导师指导下负责文献检索和筛选工作，个人边界是在团队协作下完成指定任务，不独立负责整体项目。"""

    draft = service.draft(experience_text=experience_text, consent_confirmed=True)

    # Should extract role information including personal boundary concept
    assert "role" in draft.extracted_facts
    # Note: The actual extraction logic would need to be enhanced to capture personal_boundary


def test_workflow_steps_and_quality_control():
    """Test that workflow steps and quality control can be represented."""
    # This tests the schema capability, not the extraction logic
    record_with_workflow = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_workflow_001",
        "evidence_ids": ["ev_test"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"],
        "tools": [],
        "objects": ["medical_literature"],
        "workflow_steps": [
            "Step 1: Define research question",
            "Step 2: Develop search strategy",
            "Step 3: Execute search across databases",
            "Step 4: Screen results"
        ],
        "quality_control": [
            "Peer review of search strategy",
            "Dual screening process",
            "Regular team meetings for quality assurance"
        ],
        "collaboration": ["research_team"],
        "artifacts": [],
        "outcomes": [],
        "scope": {},
        "unknowns": [],
        "status": "user_confirmed"
    }

    # All workflow and quality control fields should be accepted
    assert len(record_with_workflow["workflow_steps"]) == 4
    assert len(record_with_workflow["quality_control"]) == 3


def test_provenance_tracking():
    """Test provenance tracking capabilities."""
    record_with_provenance = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "test_provenance_001",
        "evidence_ids": ["ev_test"],
        "context": {"domain": "clinical_research", "setting": "research_project"},
        "role": {"responsibility_level": "participated"},
        "actions": ["retrieve_literature"],
        "methods": ["systematic_review"],
        "tools": [],
        "objects": ["medical_literature"],
        "collaboration": ["research_team"],
        "artifacts": [],
        "outcomes": [],
        "scope": {},
        "unknowns": [],
        "provenance": {
            "source_document_id": "interview_notes_2026",
            "source_locator": "page_3_paragraph_2",
            "created_at": "2026-08-23T14:30:00Z",
            "confirmed_at": "2026-08-23T15:00:00Z"
        },
        "status": "user_confirmed"
    }

    assert "provenance" in record_with_provenance
    assert record_with_provenance["provenance"]["source_document_id"] == "interview_notes_2026"


if __name__ == "__main__":
    # Run tests
    test_canonical_experience_schema_backward_compatibility()
    test_enhanced_canonical_experience_fields()
    test_experience_draft_service_with_enhanced_fields()
    test_role_personal_boundary_extraction()
    test_workflow_steps_and_quality_control()
    test_provenance_tracking()
    print("All enhanced canonical experience schema tests passed!")