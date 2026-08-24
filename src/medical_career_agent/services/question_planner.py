from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict


@dataclass(frozen=True)
class ClarifyingQuestion:
    """A clarifying question with quality gain score and metadata."""

    question: str
    quality_gain_score: float
    dimension: str
    fact_category: str
    evidence_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "quality_gain_score": self.quality_gain_score,
            "dimension": self.dimension,
            "fact_category": self.fact_category,
            "evidence_required": self.evidence_required
        }


class QuestionPlannerService:
    """Dynamically plans clarifying questions based on resume quality gain.

    This service implements the following rules:
    1. First generates current usable candidate positioning and resume draft
    2. Identifies missing fields that would improve resume quality
    3. Calculates quality gain for each potential question
    4. Selects up to 3 highest value questions per round
    5. Avoids repeating already answered questions
    6. Automatically stops when information is sufficient
    """

    def __init__(self, dimensions_config_path: Optional[str | Path] = None):
        """Initialize question planner with medical knowledge dimensions."""
        if dimensions_config_path is None:
            # Look for data directory relative to the repository root
            # Try multiple possible locations since we might be running from different contexts
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "data" / "medical-knowledge-dimensions.json",  # When running from src/
                Path(__file__).parent.parent.parent / "data" / "medical-knowledge-dimensions.json",      # When running from tests/
                Path("data") / "medical-knowledge-dimensions.json",                                    # When running from repo root
            ]

            dimensions_config_path = None
            for path in possible_paths:
                if path.exists():
                    dimensions_config_path = path
                    break

            if dimensions_config_path is None:
                # Fallback to the first option and let it fail with a clear error
                dimensions_config_path = Path(__file__).parent.parent.parent.parent / "data" / "medical-knowledge-dimensions.json"

        with open(dimensions_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.dimensions = config["medical_knowledge_dimensions"]

    def plan_questions(
        self,
        *,
        extracted_facts: Dict[str, Any],
        unknown_items: List[str],
        previously_asked: List[str],
        target_roles: Optional[List[str]] = None,
        experience_draft: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[ClarifyingQuestion], bool]:
        """Plan clarifying questions and determine if questioning should stop.

        Args:
            extracted_facts: Current confirmed facts from experience draft
            unknown_items: List of unknown fact categories
            previously_asked: Questions already asked in previous rounds
            target_roles: Selected target roles (affects question prioritization)
            experience_draft: Full experience draft for context

        Returns:
            Tuple of (selected questions, should_stop_questioning)
        """
        # Generate current candidate positioning to assess sufficiency
        positioning = self._generate_candidate_positioning(extracted_facts, target_roles)

        # Check if we have sufficient information to stop
        if self._is_information_sufficient(extracted_facts, positioning):
            return [], True

        # Get all potential questions from relevant dimensions
        potential_questions = self._get_potential_questions(extracted_facts, unknown_items)

        # Filter out previously asked questions
        asked_set = set(previously_asked)
        filtered_questions = [
            q for q in potential_questions
            if q.question not in asked_set
        ]

        # Calculate quality gain scores
        scored_questions = self._score_questions_by_quality_gain(
            filtered_questions, extracted_facts, target_roles, positioning
        )

        # Sort by quality gain (highest first)
        scored_questions.sort(key=lambda q: q.quality_gain_score, reverse=True)

        # Select top 3 questions
        selected_questions = scored_questions[:3]

        return selected_questions, False

    def _generate_candidate_positioning(
        self,
        extracted_facts: Dict[str, Any],
        target_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate current candidate positioning based on available facts."""
        # Determine primary dimension from context
        context = extracted_facts.get("context", {})
        domain = context.get("domain", "clinical_research")

        # Map domain to dimension name
        domain_to_dimension = {
            "clinical_research": "meta_analysis_systematic_review",
            "wet_lab": "wet_lab_research",
            "data_analysis": "data_analysis_medical",
            "medical_information": "medical_writing_literature"
        }

        dimension_name = domain_to_dimension.get(domain, "clinical_research")

        # Basic positioning elements
        positioning = {
            "has_clear_identity": False,
            "has_representative_experience": False,
            "has_methodology_depth": False,
            "has_responsibility_boundary": False,
            "has_representative_outcomes": False,
            "has_target_alignment": False,
            "information_density_score": 0.0,
            "primary_dimension": dimension_name
        }

        # Check for clear identity
        if extracted_facts.get("background") or extracted_facts.get("problem_or_goal"):
            positioning["has_clear_identity"] = True

        # Check for representative experience
        actions = extracted_facts.get("actions", [])
        methods = extracted_facts.get("methods", [])
        if actions and methods:
            positioning["has_representative_experience"] = True
            positioning["has_methodology_depth"] = True

        # Check responsibility boundary
        role_info = extracted_facts.get("role", {})
        if role_info.get("responsibility_level") and role_info.get("personal_boundary"):
            positioning["has_responsibility_boundary"] = True

        # Check for outcomes
        outcomes = extracted_facts.get("outcomes", [])
        if outcomes:
            positioning["has_representative_outcomes"] = True

        # Check target alignment (simplified)
        if target_roles:
            positioning["has_target_alignment"] = True

        # Calculate information density score
        total_fields = len([v for v in extracted_facts.values() if v])
        max_fields = 15  # Rough estimate of key fields
        positioning["information_density_score"] = min(1.0, total_fields / max_fields)

        return positioning

    def _is_information_sufficient(
        self,
        extracted_facts: Dict[str, Any],
        positioning: Dict[str, Any]
    ) -> bool:
        """Determine if current information is sufficient to stop questioning."""
        # Stop conditions based on positioning completeness
        stop_conditions = [
            positioning["has_clear_identity"],
            positioning["has_representative_experience"],
            positioning["has_responsibility_boundary"],
            positioning["has_representative_outcomes"],
            positioning["information_density_score"] >= 0.6
        ]

        # Require at least 4 out of 5 conditions to be met
        satisfied_conditions = sum(stop_conditions)
        return satisfied_conditions >= 4

    def _get_potential_questions(
        self,
        extracted_facts: Dict[str, Any],
        unknown_items: List[str]
    ) -> List[ClarifyingQuestion]:
        """Get all potential questions from relevant dimensions."""
        questions = []

        # Determine relevant dimensions
        context = extracted_facts.get("context", {})
        domain = context.get("domain", "clinical_research")

        domain_to_dimension = {
            "clinical_research": "meta_analysis_systematic_review",
            "wet_lab": "wet_lab_research",
            "data_analysis": "data_analysis_medical",
            "medical_information": "medical_writing_literature"
        }

        dimension_name = domain_to_dimension.get(domain, "clinical_research")

        if dimension_name not in self.dimensions:
            return questions

        dimension = self.dimensions[dimension_name]
        recommended_questions = dimension.get("recommended_questions", [])

        # Create questions from recommended list
        for i, question_text in enumerate(recommended_questions):
            # Map question to fact category based on position/content
            fact_category = self._map_question_to_fact_category(question_text, i)

            question = ClarifyingQuestion(
                question=question_text,
                quality_gain_score=0.0,  # Will be calculated later
                dimension=dimension_name,
                fact_category=fact_category
            )
            questions.append(question)

        return questions

    def _map_question_to_fact_category(self, question: str, index: int) -> str:
        """Map question text to fact category for scoring purposes."""
        # Simple mapping based on question content
        question_lower = question.lower()

        if any(term in question_lower for term in ["database", "search", "retrieve"]):
            return "literature_retrieval"
        elif any(term in question_lower for term in ["study", "included", "count"]):
            return "study_selection"
        elif any(term in question_lower for term in ["criteria", "inclusion", "exclusion"]):
            return "screening_criteria"
        elif any(term in question_lower for term in ["tool", "rob", "bias", "quality"]):
            return "quality_assessment"
        elif any(term in question_lower for term in ["software", "statistical", "analysis"]):
            return "statistical_analysis"
        elif any(term in question_lower for term in ["role", "responsibility", "participate"]):
            return "responsibility_boundary"
        elif any(term in question_lower for term in ["published", "presented", "manuscript"]):
            return "publication_status"
        else:
            return f"general_{index}"

    def _score_questions_by_quality_gain(
        self,
        questions: List[ClarifyingQuestion],
        extracted_facts: Dict[str, Any],
        target_roles: Optional[List[str]],
        positioning: Dict[str, Any]
    ) -> List[ClarifyingQuestion]:
        """Score questions based on their potential to improve resume quality."""
        scored_questions = []

        for question in questions:
            base_score = self._get_base_quality_gain(question.fact_category, positioning)

            # Adjust score based on target roles
            role_adjustment = 0.0
            if target_roles:
                role_adjustment = self._get_role_specific_adjustment(
                    question.dimension, question.fact_category, target_roles
                )

            # Adjust score based on current fact completeness
            completeness_adjustment = self._get_completeness_adjustment(
                question.fact_category, extracted_facts
            )

            final_score = base_score + role_adjustment + completeness_adjustment

            # Ensure non-negative score
            final_score = max(0.1, final_score)

            scored_question = ClarifyingQuestion(
                question=question.question,
                quality_gain_score=final_score,
                dimension=question.dimension,
                fact_category=question.fact_category,
                evidence_required=self._requires_evidence(question.fact_category)
            )
            scored_questions.append(scored_question)

        return scored_questions

    def _get_base_quality_gain(self, fact_category: str, positioning: Dict[str, Any]) -> float:
        """Get base quality gain score based on fact category importance."""
        # Base scores for different fact categories (higher = more important)
        base_scores = {
            "literature_retrieval": 0.8,
            "study_selection": 0.7,
            "screening_criteria": 0.6,
            "quality_assessment": 0.9,
            "statistical_analysis": 0.85,
            "responsibility_boundary": 1.0,  # Critical for authenticity
            "publication_status": 0.75,
            "general_0": 0.5,
            "general_1": 0.4,
            "general_2": 0.3,
            "general_3": 0.2,
            "general_4": 0.1,
            "general_5": 0.1,
            "general_6": 0.1
        }

        base_score = base_scores.get(fact_category, 0.3)

        # Reduce score if positioning already has this aspect covered
        if fact_category == "responsibility_boundary" and positioning["has_responsibility_boundary"]:
            base_score *= 0.3
        elif fact_category in ["literature_retrieval", "study_selection"] and positioning["has_methodology_depth"]:
            base_score *= 0.5
        elif fact_category == "publication_status" and positioning["has_representative_outcomes"]:
            base_score *= 0.4

        return base_score

    def _get_role_specific_adjustment(
        self,
        dimension: str,
        fact_category: str,
        target_roles: List[str]
    ) -> float:
        """Get role-specific adjustment to question importance."""
        # Role-specific priorities
        role_priorities = {
            "doctoral_v1": ["quality_assessment", "statistical_analysis", "publication_status"],
            "clinical_research_v1": ["literature_retrieval", "study_selection", "responsibility_boundary"],
            "medical_affairs_v1": ["quality_assessment", "publication_status", "statistical_analysis"],
            "health_ai_data_v1": ["statistical_analysis", "literature_retrieval", "study_selection"]
        }

        adjustment = 0.0
        for role in target_roles:
            if role in role_priorities and fact_category in role_priorities[role]:
                adjustment += 0.2

        return adjustment

    def _get_completeness_adjustment(self, fact_category: str, extracted_facts: Dict[str, Any]) -> float:
        """Adjust score based on how complete current facts are for this category."""
        # If we already have some facts in this area, reduce the gain
        completeness_map = {
            "literature_retrieval": len(extracted_facts.get("tools", [])),
            "study_selection": len(extracted_facts.get("scope", {}).get("study_count", "")) > 0,
            "screening_criteria": len(extracted_facts.get("methods", [])),
            "quality_assessment": "Cochrane" in str(extracted_facts.get("methods", [])),
            "statistical_analysis": len([t for t in extracted_facts.get("tools", []) if t in ["r", "spss", "sas"]]),
            "responsibility_boundary": extracted_facts.get("role", {}).get("personal_boundary") is not None,
            "publication_status": len(extracted_facts.get("outcomes", [])) > 0
        }

        if fact_category in completeness_map:
            if completeness_map[fact_category]:
                return -0.3  # Already have some info, less gain
            else:
                return 0.1   # Missing completely, higher gain
        else:
            return 0.0

    def _requires_evidence(self, fact_category: str) -> bool:
        """Determine if answering this question requires additional evidence."""
        # Questions about numbers, publications, or specific tools require evidence
        evidence_required_categories = [
            "study_selection", "publication_status", "statistical_analysis"
        ]
        return fact_category in evidence_required_categories


# Example usage and testing
if __name__ == "__main__":
    # Test the question planner
    planner = QuestionPlannerService()

    # Test with minimal facts
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

    print(f"Should stop questioning: {should_stop}")
    print(f"Selected questions ({len(questions)}):")
    for q in questions:
        print(f"  - {q.question} (score: {q.quality_gain_score:.2f})")

    # Test with sufficient facts
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

    questions2, should_stop2 = planner.plan_questions(
        extracted_facts=sufficient_facts,
        unknown_items=[],
        previously_asked=[]
    )

    print(f"\nWith sufficient facts - Should stop: {should_stop2}")
    print(f"Questions: {len(questions2)}")