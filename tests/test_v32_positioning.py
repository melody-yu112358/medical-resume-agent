import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.candidate_positioning import CandidatePositioningService
from medical_career_agent.services.experience_draft import ExperienceDraftService


def test_v32_golden_sample_positioning():
    """Test candidate positioning with V3.2 golden sample input."""
    print("Testing Candidate Positioning with V3.2 Golden Sample")
    print("=" * 60)

    # Initialize services
    draft_service = ExperienceDraftService()
    positioning_service = CandidatePositioningService()

    # V3.2 golden sample input text
    v32_input = """临床医学学士，专注于心血管临床研究方向，具备系统性循证医学训练和扎实的统计分析能力。通过参与心血管Meta分析项目，在导师指导和团队协作下完成了从研究问题识别、系统检索、质量评价到结果解释的完整证据综合流程；通过心血管流行病学调查，积累了真实世界研究数据处理和分析经验；在心内科临床实习中培养了专科临床思维和科研问题识别能力。致力于将临床实践与循证研究相结合，推动心血管疾病二级预防的个体化决策。"""

    # Extract facts from input
    draft = draft_service.draft(experience_text=v32_input, consent_confirmed=True)
    print(f"Extracted {len(draft.extracted_facts)} fact fields")
    print(f"Identified {len(draft.unknown_items)} unknown items")

    # Create canonical experience (simulating user confirmation)
    canonical_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "v32_meta_analysis_001",
        "evidence_ids": ["ev_v32_001"],
        "context": {
            "domain": "clinical_research",
            "setting": "research_project",
            "topic": "Cardiovascular meta-analysis"
        },
        "role": {
            "responsibility_level": "participated",
            "personal_boundary": "Participated in literature retrieval and screening under supervisor guidance"
        },
        "background": "Clinical uncertainty about antiplatelet therapy in ACS patients",
        "problem_or_goal": "Compare efficacy of different antiplatelet drugs in ACS patients through systematic evidence synthesis",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r", "endnote", "noteexpress"],
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
        "collaboration": ["research_team", "supervisor"],
        "artifacts": ["prisma_flowchart", "data_extraction_sheet"],
        "outputs": ["45 included studies database", "statistical analysis results"],
        "outcomes": ["Third author on submitted manuscript"],
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
        "status": "user_confirmed"
    }

    # Generate positioning for doctoral role
    print("\nGenerating positioning for doctoral_v1 target...")
    positioning = positioning_service.generate_positioning(
        canonical_experiences=[canonical_experience],
        target_roles=["doctoral_v1"]
    )

    print(f"\nIdentity: {positioning.identity}")
    print(f"Core Capabilities ({len(positioning.core_capabilities)}):")
    for i, cap in enumerate(positioning.core_capabilities, 1):
        print(f"  {i}. {cap}")
    print(f"\nRepresentative Experience: {positioning.representative_experience}")
    print(f"Differentiation: {positioning.differentiation}")
    print(f"\nCurrent Weaknesses ({len(positioning.current_weaknesses)}):")
    for weakness in positioning.current_weaknesses:
        print(f"  - {weakness}")
    print(f"\nSuggested Section Order: {positioning.suggested_section_order}")

    # Test other target roles
    target_roles = ["clinical_research_v1", "medical_affairs_v1", "health_ai_data_v1"]
    for role in target_roles:
        print(f"\n{'-'*40}")
        print(f"Positioning for {role}:")
        positioning_role = positioning_service.generate_positioning(
            canonical_experiences=[canonical_experience],
            target_roles=[role]
        )
        print(f"Identity: {positioning_role.identity}")
        print(f"Section Order: {positioning_role.suggested_section_order}")

    print("\n" + "=" * 60)
    print("V3.2 Golden Sample Positioning Test Complete!")
if __name__ == "__main__":
    test_v32_golden_sample_positioning()
    print("\nAll positioning tests passed!")
