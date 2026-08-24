import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.content_planning import ContentPlanningService


def test_v32_golden_sample_content_planning():
    """Test content planning with V3.2 golden sample canonical experience."""
    print("Testing Content Planning with V3.2 Golden Sample")
    print("=" * 60)

    # Initialize service
    service = ContentPlanningService()

    # V3.2 canonical experience (enhanced format)
    v32_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "v32_meta_analysis_001",
        "evidence_ids": ["ev_v32_001"],
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
        "difficulties": [
            "Managing large volume of retrieved studies",
            "Resolving ambiguous inclusion criteria cases"
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

    # Test all four target roles
    target_roles = ["doctoral_v1", "clinical_research_v1", "medical_affairs_v1", "health_ai_data_v1"]

    for role in target_roles:
        print(f"\n{'-'*40}")
        print(f"Content Plan for {role}:")

        # Create role-specific positioning
        if role == "doctoral_v1":
            positioning = {
                "identity": "Evidence synthesis researcher focused on cardiovascular clinical research",
                "core_capabilities": [
                    "Systematic review methodology", "Meta-analysis statistical synthesis",
                    "PRISMA-compliant study screening", "R statistical programming",
                    "SPSS statistical analysis", "Systematic literature retrieval"
                ],
                "representative_experience": "Cardiovascular meta-analysis project",
                "experience_mainline": "Focused on evidence synthesis and clinical research methodology",
                "differentiation": "Deep expertise in executing systematic evidence synthesis with rigorous methodology",
                "current_weaknesses": ["Primarily participated rather than led projects"],
                "worth_supplementing_facts": ["Publication status details", "Statistical analysis depth"],
                "suggested_section_order": ["Research Experience", "Education", "Publications", "Skills", "Clinical Experience"],
                "resume_appropriate_content": ["Methodology", "Results", "Tools", "Quality Control"],
                "interview_only_content": ["Team dynamics", "Problem-solving approaches", "Learning moments"],
                "evidence_ids": ["ev_v32_001"]
            }
        elif role == "clinical_research_v1":
            positioning = {
                "identity": "Clinical research specialist in cardiovascular research",
                "core_capabilities": [
                    "Clinical research protocols", "Data quality management",
                    "PRISMA-compliant screening", "Evidence synthesis methodology"
                ],
                "representative_experience": "Cardiovascular meta-analysis project",
                "experience_mainline": "Clinical research execution with methodological rigor",
                "differentiation": "Strong foundation in clinical research methodology with execution focus",
                "current_weaknesses": ["Limited independent project leadership"],
                "worth_supplementing_facts": ["Protocol execution details", "Data quality measures"],
                "suggested_section_order": ["Clinical Experience", "Research Experience", "Education", "Skills", "Publications"],
                "resume_appropriate_content": ["Clinical Research", "Protocol Execution", "Data Quality"],
                "interview_only_content": ["Team collaboration", "Problem resolution"],
                "evidence_ids": ["ev_v32_001"]
            }
        elif role == "medical_affairs_v1":
            positioning = {
                "identity": "Medical evidence communicator specializing in cardiovascular therapeutics",
                "core_capabilities": [
                    "Evidence synthesis", "Scientific communication",
                    "Therapeutic area expertise", "Literature analysis"
                ],
                "representative_experience": "Cardiovascular meta-analysis project",
                "experience_mainline": "Evidence synthesis and communication focus",
                "differentiation": "Ability to synthesize complex medical evidence for stakeholder communication",
                "current_weaknesses": ["Limited direct stakeholder engagement experience"],
                "worth_supplementing_facts": ["Evidence communication examples", "Stakeholder interaction"],
                "suggested_section_order": ["Research Experience", "Publications", "Education", "Skills", "Clinical Experience"],
                "resume_appropriate_content": ["Evidence Synthesis", "Scientific Writing", "Therapeutic Expertise"],
                "interview_only_content": ["Communication strategies", "Stakeholder insights"],
                "evidence_ids": ["ev_v32_001"]
            }
        else:  # health_ai_data_v1
            positioning = {
                "identity": "Healthcare data specialist with cardiovascular research expertise",
                "core_capabilities": [
                    "Statistical analysis", "Data curation",
                    "R programming", "SPSS analysis", "Systematic data collection"
                ],
                "representative_experience": "Cardiovascular meta-analysis project",
                "experience_mainline": "Data science approach to medical evidence synthesis",
                "differentiation": "Combines medical domain knowledge with systematic data analysis skills",
                "current_weaknesses": ["Limited advanced machine learning experience"],
                "worth_supplementing_facts": ["Advanced analytical techniques", "Data pipeline development"],
                "suggested_section_order": ["Skills", "Research Experience", "Education", "Publications", "Clinical Experience"],
                "resume_appropriate_content": ["Technical Skills", "Data Analysis", "Statistical Methods"],
                "interview_only_content": ["Analytical problem-solving", "Data quality approaches"],
                "evidence_ids": ["ev_v32_001"]
            }

        # Create content plan
        content_plan = service.create_content_plan(
            canonical_experiences=[v32_experience],
            candidate_positioning=positioning,
            target_role=role
        )

        print(f"Total Bullet Target: {content_plan.total_bullet_target}")
        print(f"Information Density: {content_plan.information_density_score:.2f}")
        print(f"Suggested Section Order: {content_plan.suggested_section_order}")

        # Check experience plan details
        exp_plan = content_plan.experience_plans[0]
        print(f"Experience Priority: {exp_plan.priority}")
        print(f"Bullet Count Target: {exp_plan.bullet_count_target}")
        print(f"Dimension Coverage: {len(exp_plan.dimension_coverage)} dimensions")
        print(f"Representative Contribution: {exp_plan.representative_contribution[:60]}...")

        # Verify requirements
        # All roles should get 7-9 bullets for this rich meta-analysis experience
        assert 7 <= exp_plan.bullet_count_target <= 9, f"All roles should have 7-9 bullets for rich meta-analysis, got {exp_plan.bullet_count_target}"

        assert len(exp_plan.dimension_coverage) >= 6, f"Should cover at least 6 dimensions, got {len(exp_plan.dimension_coverage)}"

    print("\n" + "=" * 60)
    print("V3.2 Golden Sample Content Planning Test Complete!")
    return True


if __name__ == "__main__":
    success = test_v32_golden_sample_content_planning()
    if success:
        print("\nAll content planning tests passed!")
    else:
        print("\nSome tests failed!")
        sys.exit(1)