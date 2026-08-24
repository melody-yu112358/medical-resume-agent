from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExperienceContentPlan:
    """Content plan for a single experience in the resume."""

    experience_id: str
    retain_reason: str
    priority: int
    bullet_count_target: int
    dimension_coverage: List[str]
    representative_contribution: str
    methodology_bullet: str
    quality_control_bullet: str
    results_or_outputs_bullet: str
    role_value_bullet: str
    content_to_exclude: List[str]
    suitable_for_resume: bool
    evidence_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "retain_reason": self.retain_reason,
            "priority": self.priority,
            "bullet_count_target": self.bullet_count_target,
            "dimension_coverage": self.dimension_coverage,
            "representative_contribution": self.representative_contribution,
            "methodology_bullet": self.methodology_bullet,
            "quality_control_bullet": self.quality_control_bullet,
            "results_or_outputs_bullet": self.results_or_outputs_bullet,
            "role_value_bullet": self.role_value_bullet,
            "content_to_exclude": self.content_to_exclude,
            "suitable_for_resume": self.suitable_for_resume,
            "evidence_ids": self.evidence_ids
        }


@dataclass(frozen=True)
class ResumeContentPlan:
    """Complete resume content plan with all experiences."""

    target_role: str
    candidate_positioning: Dict[str, Any]
    experience_plans: List[ExperienceContentPlan]
    suggested_section_order: List[str]
    total_bullet_target: int
    information_density_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_role": self.target_role,
            "candidate_positioning": self.candidate_positioning,
            "experience_plans": [plan.to_dict() for plan in self.experience_plans],
            "suggested_section_order": self.suggested_section_order,
            "total_bullet_target": self.total_bullet_target,
            "information_density_score": self.information_density_score
        }


class ContentPlanningService:
    """Creates role-aware resume content plans from candidate positioning and canonical experiences.

    This service implements the following requirements:
    - Meta-analysis experiences target 7-9 different dimensions
    - Secondary projects target 4-6 dimensions
    - Clinical internships target 4-6 dimensions
    - Dynamic adjustment based on actual information availability
    - No repetitive content around same facts
    - Clear exclusion of unsuitable content
    - Drives subsequent three-tier expression generation
    """

    def __init__(self, dimensions_config_path: Optional[str | Path] = None):
        """Initialize with medical knowledge dimensions."""
        if dimensions_config_path is None:
            dimensions_config_path = self._find_dimensions_config()

        with open(dimensions_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.dimensions = config["medical_knowledge_dimensions"]

    def _find_dimensions_config(self) -> Path:
        """Find medical knowledge dimensions config in multiple possible locations."""
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data" / "medical-knowledge-dimensions.json",
            Path(__file__).parent.parent.parent / "data" / "medical-knowledge-dimensions.json",
            Path("data") / "medical-knowledge-dimensions.json",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return Path(__file__).parent.parent.parent.parent / "data" / "medical-knowledge-dimensions.json"

    def create_content_plan(
        self,
        *,
        canonical_experiences: List[Dict[str, Any]],
        candidate_positioning: Dict[str, Any],
        target_role: str
    ) -> ResumeContentPlan:
        """Create comprehensive content plan for resume generation.

        Args:
            canonical_experiences: List of confirmed canonical experience records
            candidate_positioning: Generated candidate positioning object/dict
            target_role: Specific target role direction

        Returns:
            Complete resume content plan
        """
        # Validate inputs
        if not canonical_experiences:
            raise ValueError("At least one canonical experience is required")

        if not candidate_positioning:
            raise ValueError("Candidate positioning is required")

        if not target_role:
            raise ValueError("Target role is required")

        # Create individual experience plans
        experience_plans = []
        total_bullets = 0

        for exp in canonical_experiences:
            plan = self._create_experience_plan(exp, candidate_positioning, target_role)
            if plan.suitable_for_resume:
                experience_plans.append(plan)
                total_bullets += plan.bullet_count_target

        # Sort by priority (highest first)
        experience_plans.sort(key=lambda p: p.priority, reverse=True)

        # Calculate information density score
        density_score = min(1.0, total_bullets / 20.0)  # Normalize to 0-1 scale

        return ResumeContentPlan(
            target_role=target_role,
            candidate_positioning=candidate_positioning,
            experience_plans=experience_plans,
            suggested_section_order=candidate_positioning.get("suggested_section_order", []),
            total_bullet_target=total_bullets,
            information_density_score=density_score
        )

    def _create_experience_plan(
        self,
        experience: Dict[str, Any],
        positioning: Dict[str, Any],
        target_role: str
    ) -> ExperienceContentPlan:
        """Create content plan for a single experience."""
        experience_id = experience.get("experience_id", "unknown")
        evidence_ids = experience.get("evidence_ids", [])
        context = experience.get("context", {})
        domain = context.get("domain", "clinical_research")

        # Determine if this experience should be retained
        retain_reason, suitable = self._determine_retain_reason(experience, positioning, target_role)
        if not suitable:
            return ExperienceContentPlan(
                experience_id=experience_id,
                retain_reason=retain_reason,
                priority=0,
                bullet_count_target=0,
                dimension_coverage=[],
                representative_contribution="",
                methodology_bullet="",
                quality_control_bullet="",
                results_or_outputs_bullet="",
                role_value_bullet="",
                content_to_exclude=["Not suitable for resume"],
                suitable_for_resume=False,
                evidence_ids=evidence_ids
            )

        # Determine priority based on alignment with positioning
        priority = self._calculate_priority(experience, positioning, target_role)

        # Determine bullet count target based on experience type and information richness
        bullet_count = self._determine_bullet_count(experience, domain, target_role)

        # Identify dimension coverage based on available facts
        dimensions = self._identify_dimension_coverage(experience, domain)

        # Create specific bullet guidance
        methodology_guidance = self._create_methodology_guidance(experience, domain)
        quality_control_guidance = self._create_quality_control_guidance(experience, domain)
        results_guidance = self._create_results_guidance(experience, domain)
        role_value_guidance = self._create_role_value_guidance(experience, domain, target_role)

        # Identify representative contribution
        rep_contribution = self._identify_representative_contribution(experience, domain)

        # Identify content to exclude
        exclude_content = self._identify_excluded_content(experience, positioning)

        return ExperienceContentPlan(
            experience_id=experience_id,
            retain_reason=retain_reason,
            priority=priority,
            bullet_count_target=bullet_count,
            dimension_coverage=dimensions,
            representative_contribution=rep_contribution,
            methodology_bullet=methodology_guidance,
            quality_control_bullet=quality_control_guidance,
            results_or_outputs_bullet=results_guidance,
            role_value_bullet=role_value_guidance,
            content_to_exclude=exclude_content,
            suitable_for_resume=True,
            evidence_ids=evidence_ids
        )

    def _determine_retain_reason(
        self,
        experience: Dict[str, Any],
        positioning: Dict[str, Any],
        target_role: str
    ) -> tuple[str, bool]:
        """Determine why this experience should be retained and if it's suitable."""
        # Check if experience aligns with candidate identity
        identity = positioning.get("identity", "").lower()
        context = experience.get("context", {})
        domain = context.get("domain", "")

        # Always retain experiences that match primary domain
        if domain in identity or "clinical research" in identity:
            return f"Aligns with {identity} identity", True

        # Check if experience provides unique capabilities
        capabilities = positioning.get("core_capabilities", [])
        actions = experience.get("actions", [])
        methods = experience.get("methods", [])

        unique_elements = set(actions + methods)
        capability_elements = set()
        for cap in capabilities:
            capability_elements.update(cap.lower().split())

        if unique_elements & capability_elements:
            return "Provides unique capabilities mentioned in positioning", True

        # For doctoral roles, prioritize research experiences
        if target_role.startswith("doctoral") and domain in ["clinical_research", "wet_lab", "data_analysis"]:
            return "Research experience valuable for doctoral applications", True

        # For clinical roles, prioritize clinical experiences
        if target_role.startswith("clinical_research") and domain == "clinical_research":
            return "Clinical research experience directly relevant", True

        # Default: retain but with lower priority
        return "General professional experience", True

    def _calculate_priority(
        self,
        experience: Dict[str, Any],
        positioning: Dict[str, Any],
        target_role: str
    ) -> int:
        """Calculate priority score (1-10) for experience retention."""
        priority = 5  # Base priority

        # Boost for representative experience
        rep_exp = positioning.get("representative_experience", "").lower()
        topic = experience.get("context", {}).get("topic", "") or ""
        if topic and topic in rep_exp:
            priority += 3

        # Boost for domain alignment
        identity = positioning.get("identity", "").lower()
        domain = experience.get("context", {}).get("domain", "")
        if domain in identity:
            priority += 2

        # Role-specific boosts
        if target_role.startswith("doctoral"):
            # Prioritize experiences with outcomes and publications
            if experience.get("outcomes"):
                priority += 2
            if len([v for v in experience.values() if v]) >= 10:  # Rich experience
                priority += 1

        elif target_role.startswith("clinical_research"):
            # Prioritize clinical trial and patient-facing experiences
            setting = experience.get("context", {}).get("setting", "")
            if setting in ["clinical_trial", "clinical_practice"]:
                priority += 2

        elif target_role.startswith("medical_affairs"):
            # Prioritize literature synthesis and communication experiences
            if "medical_information" in domain or experience.get("actions", []):
                if any(action in ["review_literature", "write_manuscript"] for action in experience.get("actions", [])):
                    priority += 2

        elif target_role.startswith("health_ai_data"):
            # Prioritize data analysis and technical experiences
            tools = experience.get("tools", [])
            if any(tool in ["python", "r", "sql", "spss"] for tool in tools):
                priority += 2

        return min(10, max(1, priority))

    def _determine_bullet_count(
        self,
        experience: Dict[str, Any],
        domain: str,
        target_role: str
    ) -> int:
        """Determine target bullet count based on experience type and richness."""
        # Count available information fields
        info_fields = len([v for v in experience.values() if v and v != experience.get("experience_id")])

        # Base counts by domain
        if domain == "clinical_research":
            if "meta_analysis" in str(experience.get("methods", [])):
                base_count = 8  # Meta-analysis gets higher count
            else:
                base_count = 6
        elif domain == "wet_lab":
            base_count = 5
        elif domain == "data_analysis":
            base_count = 6
        elif domain == "medical_information":
            base_count = 5
        elif domain == "clinical_practice":
            base_count = 6
        elif domain == "epidemiology_research":
            base_count = 4
        else:
            base_count = 4

        # Adjust based on information richness
        if info_fields >= 12:
            bullet_count = min(base_count + 2, 9)  # Max 9 bullets
        elif info_fields >= 8:
            bullet_count = base_count
        elif info_fields >= 5:
            bullet_count = max(base_count - 1, 3)  # Min 3 bullets
        else:
            bullet_count = 2  # Minimal experience

        # 临床实习与大创控制在 4-6 条验收范围内
        if domain in ("clinical_practice", "epidemiology_research"):
            bullet_count = min(bullet_count, 6)
            bullet_count = max(bullet_count, 4)

        # Role-specific adjustments
        if target_role.startswith("doctoral") and domain == "clinical_research":
            # Doctoral applications benefit from detailed methodology
            bullet_count = min(bullet_count + 1, 9)

        return bullet_count

    def _identify_dimension_coverage(
        self,
        experience: Dict[str, Any],
        domain: str
    ) -> List[str]:
        """Identify which dimensions are covered by this experience."""
        dimensions = []

        # Map experience fields to standard dimensions
        if experience.get("background") or experience.get("problem_or_goal"):
            dimensions.append("research_problem_identification")

        if experience.get("actions"):
            actions = experience.get("actions", [])
            if any(a in ["retrieve_literature", "screen_studies"] for a in actions):
                dimensions.append("literature_retrieval_and_screening")
            if any(a in ["extract_data", "analyze_data"] for a in actions):
                dimensions.append("data_extraction_and_analysis")

        if experience.get("methods"):
            methods = experience.get("methods", [])
            if "systematic_review" in methods:
                dimensions.append("systematic_review_methodology")
            if "meta_analysis" in methods:
                dimensions.append("meta_analysis_statistics")
            if any(m in ["randomized_trial", "cohort_study", "case_control"] for m in methods):
                dimensions.append("clinical_study_design")

        if experience.get("workflow_steps"):
            dimensions.append("research_workflow_execution")

        if experience.get("quality_control"):
            dimensions.append("quality_assurance_measures")

        if experience.get("decisions_or_judgments"):
            dimensions.append("critical_thinking_and_decisions")

        if experience.get("collaboration"):
            dimensions.append("team_collaboration")

        if experience.get("artifacts") or experience.get("outputs"):
            dimensions.append("research_deliverables")

        if experience.get("outcomes"):
            dimensions.append("research_outcomes_and_impact")

        if experience.get("insights"):
            dimensions.append("scientific_insights")

        # Ensure minimum dimension coverage
        if not dimensions:
            dimensions = ["general_research_participation"]

        return dimensions[:10]  # Limit to top 10 dimensions

    def _create_methodology_guidance(
        self,
        experience: Dict[str, Any],
        domain: str
    ) -> str:
        """Create guidance for methodology-focused bullet point."""
        methods = experience.get("methods", [])
        actions = experience.get("actions", [])
        tools = experience.get("tools", [])

        if domain == "clinical_research":
            if "systematic_review" in methods:
                return "Focus on PICO framework, systematic search strategy, and PRISMA adherence"
            elif "meta_analysis" in methods:
                return "Emphasize statistical methodology, heterogeneity assessment, and sensitivity analysis"
            else:
                return "Describe research design, protocol adherence, and methodological rigor"

        elif domain == "wet_lab":
            return "Detail experimental protocols, reagent preparation, and instrument operation"

        elif domain == "data_analysis":
            return "Highlight statistical methods, analytical approaches, and software tools"

        elif domain == "clinical_practice":
            return "Describe clinical assessment protocols, diagnostic approaches, and treatment planning"

        else:
            return "Explain methodological approach and research design"

    def _create_quality_control_guidance(
        self,
        experience: Dict[str, Any],
        domain: str
    ) -> str:
        """Create guidance for quality control-focused bullet point."""
        qc_items = experience.get("quality_control", [])

        if qc_items:
            return f"Emphasize quality measures: {', '.join(qc_items[:3])}"

        # Default quality guidance by domain
        if domain == "clinical_research":
            return "Highlight PRISMA compliance, dual screening, bias risk assessment, and standardized protocols"
        elif domain == "wet_lab":
            return "Focus on sterile technique, reagent QC, instrument calibration, and replicate design"
        elif domain == "data_analysis":
            return "Emphasize data validation, appropriate statistical methods, and reproducible analysis"
        elif domain == "clinical_practice":
            return "Highlight supervisor oversight, standardized protocols, and patient safety measures"
        else:
            return "Describe quality assurance measures and validation procedures"

    def _create_results_guidance(
        self,
        experience: Dict[str, Any],
        domain: str
    ) -> str:
        """Create guidance for results/outputs-focused bullet point."""
        outcomes = experience.get("outcomes", [])
        outputs = experience.get("outputs", [])
        artifacts = experience.get("artifacts", [])

        all_results = outcomes + outputs + artifacts

        if all_results:
            return f"Present concrete deliverables: {', '.join(all_results[:3])}"

        # Default results guidance
        if domain == "clinical_research":
            return "Describe study database, analysis results, and manuscript contributions"
        elif domain == "wet_lab":
            return "Present experimental results, data collection, and analysis findings"
        elif domain == "data_analysis":
            return "Highlight analytical insights, visualizations, and data products"
        elif domain == "clinical_practice":
            return "Describe patient interactions, clinical skills developed, and case exposure"
        else:
            return "Present research outputs and deliverables"

    def _create_role_value_guidance(
        self,
        experience: Dict[str, Any],
        domain: str,
        target_role: str
    ) -> str:
        """Create guidance for role-specific value-focused bullet point."""
        # Get role-specific value from dimensions config
        dimension_name = self._map_domain_to_dimension(domain)

        if dimension_name in self.dimensions:
            role_values = self.dimensions[dimension_name].get("role_specific_value", {})
            if target_role in role_values:
                role_value_dict = role_values[target_role]
                # Convert dict to guidance string
                value_items = list(role_value_dict.values())[:3]
                if value_items:
                    return f"Emphasize: {', '.join(value_items)}"

        # Default role value guidance
        if target_role.startswith("doctoral"):
            return "Highlight research methodology competence and academic contribution potential"
        elif target_role.startswith("clinical_research"):
            return "Emphasize protocol execution precision and data quality management"
        elif target_role.startswith("medical_affairs"):
            return "Focus on evidence synthesis capability and scientific communication"
        elif target_role.startswith("health_ai_data"):
            return "Highlight data curation skills and systematic analytical approach"
        else:
            return "Explain professional value and career relevance"

    def _map_domain_to_dimension(self, domain: str) -> str:
        """Map domain to dimension name."""
        domain_mapping = {
            "clinical_research": "meta_analysis_systematic_review",
            "wet_lab": "wet_lab_research",
            "data_analysis": "data_analysis_medical",
            "medical_information": "medical_writing_literature",
            "clinical_practice": "clinical_practice"
        }
        return domain_mapping.get(domain, "meta_analysis_systematic_review")

    def _identify_representative_contribution(
        self,
        experience: Dict[str, Any],
        domain: str
    ) -> str:
        """Identify the most representative contribution from this experience."""
        # Look for specific high-value contributions
        actions = experience.get("actions", [])
        methods = experience.get("methods", [])
        tools = experience.get("tools", [])

        if domain == "clinical_research":
            if "meta_analysis" in methods:
                return "Statistical meta-analysis and result interpretation"
            elif "systematic_review" in methods:
                return "Systematic literature retrieval and evidence synthesis"
            elif any(a in ["screen_studies", "extract_data"] for a in actions):
                return "Study screening and data extraction"

        elif domain == "wet_lab":
            if "perform_experiments" in actions:
                return "Experimental execution and data collection"

        elif domain == "data_analysis":
            if "analyze_data" in actions:
                return "Statistical analysis and result interpretation"

        elif domain == "clinical_practice":
            return "Clinical assessment and patient interaction"

        # Default contribution
        if actions:
            return f"{actions[0].replace('_', ' ')} contribution"
        else:
            return "General research participation"

    def _identify_excluded_content(
        self,
        experience: Dict[str, Any],
        positioning: Dict[str, Any]
    ) -> List[str]:
        """Identify content that should be excluded from resume."""
        excluded = []

        # Exclude interview-only content
        interview_content = positioning.get("interview_only_content", [])
        if interview_content:
            excluded.extend(interview_content)

        # Exclude vague or unsupported claims
        if experience.get("role", {}).get("responsibility_level") == "participated":
            excluded.append("Claims of independent leadership or ownership")

        # Exclude unverified outcomes
        if not experience.get("outcomes"):
            excluded.append("Speculative impact statements or unverified results")

        # Exclude redundant content
        dimensions = self._identify_dimension_coverage(experience, experience.get("context", {}).get("domain", ""))
        if len(dimensions) == 1:
            excluded.append("Repetitive descriptions of same activity")

        return excluded[:5]  # Limit to top 5 exclusions


# Example usage
if __name__ == "__main__":
    # Test the content planning service
    service = ContentPlanningService()

    # Sample canonical experience (V3.2 style)
    sample_experience = {
        "schema_version": "canonical-experience-v1",
        "experience_id": "meta_analysis_001",
        "evidence_ids": ["ev_001"],
        "context": {
            "domain": "clinical_research",
            "setting": "research_project",
            "topic": "Cardiovascular meta-analysis"
        },
        "role": {
            "responsibility_level": "participated",
            "personal_boundary": "Participated in literature retrieval under supervision"
        },
        "background": "Clinical uncertainty about antiplatelet therapy in ACS",
        "problem_or_goal": "Compare efficacy of different antiplatelet drugs",
        "actions": ["retrieve_literature", "screen_studies", "extract_data", "analyze_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r", "endnote"],
        "workflow_steps": ["PICO framework development", "Multi-database search execution"],
        "quality_control": ["Dual screening process", "Cochrane RoB application"],
        "outcomes": ["Third author on submitted manuscript"],
        "scope": {"study_count": "45"},
        "status": "user_confirmed"
    }

    # Sample positioning
    sample_positioning = {
        "identity": "Evidence synthesis researcher focused on clinical research",
        "core_capabilities": ["Systematic review methodology", "Meta-analysis statistics", "Literature retrieval"],
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

    # Create content plan
    content_plan = service.create_content_plan(
        canonical_experiences=[sample_experience],
        candidate_positioning=sample_positioning,
        target_role="doctoral_v1"
    )

    print("Content Plan Generated:")
    print(f"Target Role: {content_plan.target_role}")
    print(f"Total Bullet Target: {content_plan.total_bullet_target}")
    print(f"Information Density: {content_plan.information_density_score:.2f}")

    for plan in content_plan.experience_plans:
        print(f"\nExperience: {plan.experience_id}")
        print(f"Priority: {plan.priority}")
        print(f"Bullet Count: {plan.bullet_count_target}")
        print(f"Dimensions: {len(plan.dimension_coverage)}")
        print(f"Representative Contribution: {plan.representative_contribution}")