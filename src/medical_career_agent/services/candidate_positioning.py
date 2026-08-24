from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass(frozen=True)
class CandidatePositioning:
    """Candidate positioning with identity, capabilities, and alignment."""

    identity: str
    core_capabilities: List[str]
    representative_experience: str
    experience_mainline: str
    differentiation: str
    current_weaknesses: List[str]
    worth_supplementing_facts: List[str]
    suggested_section_order: List[str]
    resume_appropriate_content: List[str]
    interview_only_content: List[str]
    evidence_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity,
            "core_capabilities": self.core_capabilities,
            "representative_experience": self.representative_experience,
            "experience_mainline": self.experience_mainline,
            "differentiation": self.differentiation,
            "current_weaknesses": self.current_weaknesses,
            "worth_supplementing_facts": self.worth_supplementing_facts,
            "suggested_section_order": self.suggested_section_order,
            "resume_appropriate_content": self.resume_appropriate_content,
            "interview_only_content": self.interview_only_content,
            "evidence_ids": self.evidence_ids
        }


class CandidatePositioningService:
    """Generates candidate positioning based on canonical experiences and target roles.

    This service implements the following requirements:
    - Cannot just repeat user's original text
    - Cannot generate unsupported "expert"/"leader"/"owner" claims
    - Can confidently explain research potential and role value
    - Produces明显 different positioning for four target directions
    - Drives subsequent content generation through clear positioning
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

    def generate_positioning(
        self,
        *,
        canonical_experiences: List[Dict[str, Any]],
        education_background: Optional[Dict[str, Any]] = None,
        skills: Optional[List[Dict[str, Any]]] = None,
        target_roles: List[str],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> CandidatePositioning:
        """Generate comprehensive candidate positioning.

        Args:
            canonical_experiences: List of confirmed canonical experience records
            education_background: Educational information
            skills: Technical and professional skills
            target_roles: Selected target role directions
            user_preferences: User-specified preferences

        Returns:
            Complete candidate positioning object
        """
        # Validate inputs
        if not canonical_experiences:
            raise ValueError("At least one canonical experience is required")

        if not target_roles:
            raise ValueError("At least one target role is required")

        # Extract evidence IDs from all experiences
        evidence_ids = []
        for exp in canonical_experiences:
            evidence_ids.extend(exp.get("evidence_ids", []))

        # Generate core components
        identity = self._generate_identity(canonical_experiences, target_roles)
        core_capabilities = self._extract_core_capabilities(canonical_experiences, target_roles)
        representative_experience = self._identify_representative_experience(canonical_experiences)
        experience_mainline = self._create_experience_mainline(canonical_experiences)
        differentiation = self._generate_differentiation(canonical_experiences, target_roles)
        current_weaknesses = self._identify_weaknesses(canonical_experiences, target_roles)
        worth_supplementing_facts = self._identify_supplemental_facts(canonical_experiences, target_roles)
        suggested_section_order = self._determine_section_order(target_roles)
        resume_appropriate_content = self._filter_resume_content(canonical_experiences)
        interview_only_content = self._identify_interview_content(canonical_experiences)

        return CandidatePositioning(
            identity=identity,
            core_capabilities=core_capabilities,
            representative_experience=representative_experience,
            experience_mainline=experience_mainline,
            differentiation=differentiation,
            current_weaknesses=current_weaknesses,
            worth_supplementing_facts=worth_supplementing_facts,
            suggested_section_order=suggested_section_order,
            resume_appropriate_content=resume_appropriate_content,
            interview_only_content=interview_only_content,
            evidence_ids=list(set(evidence_ids))  # Remove duplicates
        )

    def _generate_identity(self, experiences: List[Dict[str, Any]], target_roles: List[str]) -> str:
        """Generate one-sentence candidate identity."""
        # Determine primary domain from experiences
        domains = set()
        for exp in experiences:
            context = exp.get("context", {})
            domain = context.get("domain", "clinical_research")
            domains.add(domain)

        primary_domain = list(domains)[0] if domains else "clinical_research"

        # Map to human-readable domain names
        domain_names = {
            "clinical_research": "clinical research",
            "wet_lab": "laboratory research",
            "data_analysis": "medical data analysis",
            "medical_information": "medical literature synthesis",
            "industry_collaboration": "industry collaboration",
            "education": "medical education"
        }

        domain_name = domain_names.get(primary_domain, primary_domain)

        # Generate identity based on target roles
        if any(role.startswith("doctoral") for role in target_roles):
            return f"Evidence synthesis researcher focused on {domain_name}"
        elif any(role.startswith("clinical_research") for role in target_roles):
            return f"Clinical research specialist in {domain_name}"
        elif any(role.startswith("medical_affairs") for role in target_roles):
            return f"Medical evidence communicator specializing in {domain_name}"
        elif any(role.startswith("health_ai_data") for role in target_roles):
            return f"Healthcare data specialist with {domain_name} expertise"
        else:
            return f"Medical professional with {domain_name} experience"

    def _extract_core_capabilities(self, experiences: List[Dict[str, Any]], target_roles: List[str]) -> List[str]:
        """Extract 3-6 core capabilities with evidence."""
        capabilities = set()

        # Extract from actions and methods
        for exp in experiences:
            actions = exp.get("actions", [])
            methods = exp.get("methods", [])
            tools = exp.get("tools", [])

            # Map actions to capabilities
            action_capabilities = {
                "retrieve_literature": "Systematic literature retrieval",
                "screen_studies": "PRISMA-compliant study screening",
                "extract_data": "Structured data extraction",
                "perform_experiments": "Laboratory experimental execution",
                "analyze_data": "Statistical data analysis",
                "write_manuscript": "Scientific manuscript writing"
            }

            for action in actions:
                if action in action_capabilities:
                    capabilities.add(action_capabilities[action])

            # Map methods to capabilities
            method_capabilities = {
                "systematic_review": "Systematic review methodology",
                "meta_analysis": "Meta-analysis statistical synthesis",
                "randomized_trial": "Clinical trial protocol execution",
                "cohort_study": "Longitudinal cohort study management",
                "case_control": "Case-control study design"
            }

            for method in methods:
                if method in method_capabilities:
                    capabilities.add(method_capabilities[method])

            # Add tool-specific capabilities
            if "r" in tools:
                capabilities.add("R statistical programming")
            if "spss" in tools:
                capabilities.add("SPSS statistical analysis")
            if "python" in tools:
                capabilities.add("Python data science")

        # Limit to 6 most relevant capabilities
        capability_list = list(capabilities)[:6]

        # If empty, provide generic capabilities based on domain
        if not capability_list:
            domains = set(exp.get("context", {}).get("domain", "clinical_research") for exp in experiences)
            primary_domain = list(domains)[0]

            if primary_domain == "clinical_research":
                capability_list = [
                    "Evidence synthesis methodology",
                    "Clinical research protocols",
                    "Scientific literature analysis"
                ]
            elif primary_domain == "wet_lab":
                capability_list = [
                    "Laboratory techniques",
                    "Experimental design",
                    "Molecular biology methods"
                ]
            elif primary_domain == "data_analysis":
                capability_list = [
                    "Statistical analysis",
                    "Data visualization",
                    "Research methodology"
                ]
            else:
                capability_list = ["Medical research", "Scientific analysis", "Evidence evaluation"]

        return capability_list

    def _identify_representative_experience(self, experiences: List[Dict[str, Any]]) -> str:
        """Identify the most representative experience."""
        if len(experiences) == 1:
            exp = experiences[0]
            context = exp.get("context", {})
            topic = context.get("topic", "medical research")
            return f"{topic} project"

        # Find experience with most comprehensive information
        best_exp = max(experiences, key=lambda e: len([v for v in e.values() if v]))
        context = best_exp.get("context", {})
        topic = context.get("topic", "comprehensive medical research")
        return f"{topic} project"

    def _create_experience_mainline(self, experiences: List[Dict[str, Any]]) -> str:
        """Create narrative connecting experiences into mainline."""
        if len(experiences) <= 1:
            return "Focused on evidence synthesis and clinical research methodology"

        # Create simple narrative based on experience types
        domains = []
        for exp in experiences:
            context = exp.get("context", {})
            domain = context.get("domain", "clinical_research")
            domains.append(domain)

        unique_domains = list(set(domains))

        if len(unique_domains) == 1:
            return f"Consistent focus on {unique_domains[0].replace('_', ' ')} throughout academic and research career"
        else:
            return "Integrated experience spanning multiple domains of medical research"

    def _generate_differentiation(self, experiences: List[Dict[str, Any]], target_roles: List[str]) -> str:
        """Generate what differentiates candidate from others."""
        # Count comprehensive experiences
        comprehensive_count = sum(
            1 for exp in experiences
            if len([v for v in exp.values() if v]) >= 8  # At least 8 fields filled
        )

        if comprehensive_count >= 2:
            return "Demonstrated ability to execute comprehensive research projects across multiple domains"
        elif comprehensive_count == 1:
            return "Deep expertise in executing systematic evidence synthesis with rigorous methodology"
        else:
            return "Strong foundation in medical research methodology with potential for advanced contribution"

    def _identify_weaknesses(self, experiences: List[Dict[str, Any]], target_roles: List[str]) -> List[str]:
        """Identify current weaknesses or gaps."""
        weaknesses = []

        # Check for missing outcomes
        has_outcomes = any(exp.get("outcomes") for exp in experiences)
        if not has_outcomes:
            weaknesses.append("Limited documented research outcomes")

        # Check for responsibility level
        responsibility_levels = set(exp.get("role", {}).get("responsibility_level") for exp in experiences)
        if "participated" in responsibility_levels and len(responsibility_levels) == 1:
            weaknesses.append("Primarily participated rather than led projects")

        # Check for publication status
        has_publications = any(
            any("publication" in str(outcome).lower() or "manuscript" in str(outcome).lower()
                for outcome in exp.get("outcomes", []))
            for exp in experiences
        )
        if not has_publications:
            weaknesses.append("Limited publication record")

        # Role-specific weaknesses
        if any(role.startswith("doctoral") for role in target_roles):
            if not has_publications:
                weaknesses.append("Needs stronger publication portfolio for doctoral applications")

        if any(role.startswith("health_ai_data") for role in target_roles):
            tools = set(tool for exp in experiences for tool in exp.get("tools", []))
            if not any(tool in ["python", "r", "sql"] for tool in tools):
                weaknesses.append("Limited programming/technical tool experience")

        return weaknesses[:3]  # Limit to top 3 weaknesses

    def _identify_supplemental_facts(self, experiences: List[Dict[str, Any]], target_roles: List[str]) -> List[str]:
        """Identify facts worth supplementing to improve positioning."""
        supplemental = []

        # Check for missing key information
        for exp in experiences:
            if not exp.get("outcomes"):
                supplemental.append("Specific research outcomes and impacts")
            if not exp.get("scope"):
                supplemental.append("Quantitative scope details (study counts, sample sizes)")
            if exp.get("role", {}).get("responsibility_level") == "participated":
                supplemental.append("Specific responsibilities and contributions within team context")

        # Role-specific supplemental facts
        if any(role.startswith("doctoral") for role in target_roles):
            supplemental.extend([
                "Publication status and authorship details",
                "Statistical analysis depth and complexity",
                "Research independence and methodology decisions"
            ])

        if any(role.startswith("medical_affairs") for role in target_roles):
            supplemental.extend([
                "Evidence communication and presentation experience",
                "Stakeholder engagement examples",
                "Therapeutic area expertise depth"
            ])

        return list(set(supplemental))[:5]  # Deduplicate and limit

    def _determine_section_order(self, target_roles: List[str]) -> List[str]:
        """Determine suggested section order based on target roles."""
        base_order = ["Education", "Research Experience", "Clinical Experience", "Skills", "Publications"]

        if any(role.startswith("doctoral") for role in target_roles):
            return ["Research Experience", "Education", "Publications", "Skills", "Clinical Experience"]
        elif any(role.startswith("clinical_research") for role in target_roles):
            return ["Clinical Experience", "Research Experience", "Education", "Skills", "Publications"]
        elif any(role.startswith("medical_affairs") for role in target_roles):
            return ["Research Experience", "Publications", "Education", "Skills", "Clinical Experience"]
        elif any(role.startswith("health_ai_data") for role in target_roles):
            return ["Skills", "Research Experience", "Education", "Publications", "Clinical Experience"]
        else:
            return base_order

    def _filter_resume_content(self, experiences: List[Dict[str, Any]]) -> List[str]:
        """Filter content appropriate for resume (vs interview only)."""
        resume_content = []

        for exp in experiences:
            # Always include confirmed facts
            if exp.get("background"):
                resume_content.append("Research background and problem identification")
            if exp.get("actions"):
                resume_content.append("Specific research actions and methodologies")
            if exp.get("methods"):
                resume_content.append("Research methods and protocols")
            if exp.get("tools"):
                resume_content.append("Technical tools and software")
            if exp.get("outcomes"):
                resume_content.append("Documented research outcomes")
            if exp.get("scope"):
                resume_content.append("Quantitative scope and scale")

        return list(set(resume_content))

    def _identify_interview_content(self, experiences: List[Dict[str, Any]]) -> List[str]:
        """Identify content better suited for interviews than resume."""
        interview_content = []

        for exp in experiences:
            # Soft skills and learning experiences
            if exp.get("difficulties"):
                interview_content.append("Problem-solving approaches and overcoming challenges")
            if exp.get("insights"):
                interview_content.append("Key research insights and learning moments")
            if exp.get("decisions_or_judgments"):
                interview_content.append("Critical thinking and decision-making examples")
            if exp.get("collaboration"):
                interview_content.append("Team dynamics and collaboration experiences")

        return list(set(interview_content))


# Example usage
if __name__ == "__main__":
    # Test the positioning service
    service = CandidatePositioningService()

    # Sample canonical experience (similar to V3.2)
    sample_experience = {
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
        "problem_or_goal": "Compare efficacy of different antiplatelet drugs in ACS patients",
        "actions": ["retrieve_literature", "screen_studies", "extract_data"],
        "methods": ["systematic_review", "meta_analysis"],
        "tools": ["spss", "r", "endnote"],
        "objects": ["medical_literature", "clinical_studies"],
        "workflow_steps": [
            "Develop PICO framework with supervisor",
            "Execute multi-database search strategy"
        ],
        "quality_control": ["Dual screening process", "Cochrane RoB tool application"],
        "collaboration": ["research_team", "supervisor"],
        "artifacts": ["prisma_flowchart", "data_extraction_sheet"],
        "outcomes": ["Third author on submitted manuscript"],
        "scope": {"database_count": "3", "study_count": "45"},
        "status": "user_confirmed"
    }

    positioning = service.generate_positioning(
        canonical_experiences=[sample_experience],
        target_roles=["doctoral_v1"]
    )

    print("Candidate Positioning Generated:")
    print(f"Identity: {positioning.identity}")
    print(f"Core Capabilities: {positioning.core_capabilities}")
    print(f"Representative Experience: {positioning.representative_experience}")
    print(f"Differentiation: {positioning.differentiation}")
    print(f"Weaknesses: {positioning.current_weaknesses}")