from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .bullet_composer import BulletClaim


@dataclass(frozen=True)
class ClaimGateResult:
    """Result of claim gate validation."""

    status: str  # "ready", "needs_confirmation", or "rejected"
    failed_checks: List[str]
    risk_flags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "failed_checks": self.failed_checks,
            "risk_flags": self.risk_flags,
        }


class ClaimGateService:
    """Validates bullet claims against twelve deterministic checks.

    The twelve checks are:
    1. Evidence exists
    2. Evidence belongs to current experience
    3. Used facts have been confirmed
    4. Actions have evidence
    5. Methods have evidence
    6. Tools have evidence
    7. Numbers match exactly
    8. Outcomes have evidence
    9. Responsibility level not upgraded
    10. No forbidden role pack expressions
    11. Role value not disguised as factual outcome
    12. User edits don't introduce unconfirmed facts
    """

    def __init__(self, role_packs_dir: str | Path | None = None):
        self.role_packs_dir = Path(role_packs_dir) if role_packs_dir else Path(__file__).parent.parent.parent.parent / "data" / "role-packs"

    def validate_claim(
        self,
        *,
        bullet_claim: Dict[str, Any],
        canonical_experience: Dict[str, Any],
    ) -> ClaimGateResult:
        """Validate a bullet claim against the twelve deterministic checks.

        Args:
            bullet_claim: A bullet claim dictionary (bullet-claim-v1 schema)
            canonical_experience: The canonical experience it's based on (canonical-experience-v1 schema)

        Returns:
            ClaimGateResult with status and any failed checks
        """
        # Validate input schemas
        if bullet_claim.get("schema_version") != "bullet-claim-v1":
            raise ValueError("bullet_claim must use bullet-claim-v1 schema")

        if canonical_experience.get("schema_version") != "canonical-experience-v1":
            raise ValueError("canonical_experience must use canonical-experience-v1 schema")

        if canonical_experience.get("status") != "user_confirmed":
            raise ValueError("canonical_experience must have status 'user_confirmed'")

        # Initialize results
        failed_checks = []
        risk_flags = list(bullet_claim.get("risk_flags", []))

        # Get role pack
        try:
            role_pack = self._load_role_pack(bullet_claim["role_pack"])
        except ValueError as e:
            failed_checks.append(f"role_pack_load_error: {e}")
            return ClaimGateResult(status="rejected", failed_checks=failed_checks, risk_flags=risk_flags)

        # Perform the twelve checks
        check_results = [
            self._check_evidence_exists(bullet_claim),
            self._check_evidence_belongs_to_experience(bullet_claim, canonical_experience),
            self._check_used_facts_confirmed(bullet_claim, canonical_experience),
            self._check_actions_have_evidence(bullet_claim, canonical_experience),
            self._check_methods_have_evidence(bullet_claim, canonical_experience),
            self._check_tools_have_evidence(bullet_claim, canonical_experience),
            self._check_numbers_match_exactly(bullet_claim, canonical_experience),
            self._check_outcomes_have_evidence(bullet_claim, canonical_experience),
            self._check_responsibility_not_upgraded(bullet_claim, canonical_experience),
            self._check_no_forbidden_expressions(bullet_claim, role_pack),
            self._check_role_value_not_disguised_as_outcome(bullet_claim, role_pack),
            self._check_user_edits_no_unconfirmed_facts(bullet_claim, canonical_experience),
        ]

        # Collect failed checks
        for check_name, (passed, message) in zip(self._get_check_names(), check_results):
            if not passed:
                failed_checks.append(f"{check_name}: {message}")

        # Determine status
        if len(failed_checks) == 0:
            status = "ready"
        elif any("rejected" in fc for fc in failed_checks):
            status = "rejected"
        else:
            status = "needs_confirmation"

        return ClaimGateResult(status=status, failed_checks=failed_checks, risk_flags=risk_flags)

    def _get_check_names(self) -> List[str]:
        """Get the names of the twelve checks."""
        return [
            "evidence_exists",
            "evidence_belongs_to_current_experience",
            "used_facts_confirmed",
            "actions_have_evidence",
            "methods_have_evidence",
            "tools_have_evidence",
            "numbers_match_exactly",
            "outcomes_have_evidence",
            "responsibility_not_upgraded",
            "no_forbidden_role_pack_expressions",
            "role_value_not_disguised_as_factual_outcome",
            "user_edits_no_unconfirmed_facts",
        ]

    def _load_role_pack(self, role_pack_name: str) -> Dict[str, Any]:
        """Load role pack configuration from JSON file."""
        role_pack_path = self.role_packs_dir / f"{role_pack_name}.json"
        if not role_pack_path.exists():
            raise ValueError(f"Role pack '{role_pack_name}' not found at {role_pack_path}")

        try:
            return json.loads(role_pack_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(f"Failed to load role pack '{role_pack_name}': {e}")

    def _check_evidence_exists(self, bullet_claim: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 1: Evidence exists."""
        evidence_ids = bullet_claim.get("evidence_ids", [])
        if not evidence_ids:
            return False, "No evidence IDs provided"
        return True, ""

    def _check_evidence_belongs_to_experience(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 2: Evidence belongs to current experience."""
        claim_evidence = set(bullet_claim.get("evidence_ids", []))
        experience_evidence = set(canonical_experience.get("evidence_ids", []))

        if not claim_evidence.issubset(experience_evidence):
            extra_evidence = claim_evidence - experience_evidence
            return False, f"Evidence IDs {list(extra_evidence)} do not belong to this experience"
        return True, ""

    def _check_used_facts_confirmed(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 3: Used facts have been confirmed."""
        used_facts = bullet_claim.get("used_facts", [])
        if not used_facts:
            return True, ""  # No used facts is acceptable

        # Extract all confirmed facts from canonical experience
        confirmed_facts = self._extract_all_confirmed_facts(canonical_experience)

        # Check each used fact
        for used_fact in used_facts:
            if ":" not in used_fact:
                continue  # Skip malformed facts

            category, value = used_fact.split(":", 1)
            if category in ["context", "role"]:
                # Handle nested objects
                if "." in category:
                    obj_cat, field = category.split(".", 1)
                    if obj_cat in confirmed_facts and field in confirmed_facts[obj_cat]:
                        if str(confirmed_facts[obj_cat][field]) != value:
                            return False, f"Used fact {used_fact} does not match confirmed value"
                else:
                    if category in confirmed_facts and str(confirmed_facts[category]) != value:
                        return False, f"Used fact {used_fact} does not match confirmed value"
            else:
                # Handle array categories
                if category in confirmed_facts:
                    if value not in confirmed_facts[category]:
                        return False, f"Used fact {used_fact} not found in confirmed facts"
                else:
                    return False, f"Used fact category {category} not found in confirmed facts"

        return True, ""

    def _extract_all_confirmed_facts(self, canonical_experience: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all confirmed facts from canonical experience."""
        facts = {}

        # Copy all top-level fields that contain facts
        array_fields = ["actions", "methods", "tools", "objects", "collaboration", "artifacts", "outcomes"]
        for field in array_fields:
            facts[field] = canonical_experience.get(field, [])

        # Copy context and role objects
        facts["context"] = canonical_experience.get("context", {})
        facts["role"] = canonical_experience.get("role", {})
        facts["scope"] = canonical_experience.get("scope", {})

        return facts

    def _check_actions_have_evidence(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 4: Actions have evidence."""
        used_facts = bullet_claim.get("used_facts", [])
        actions_in_claim = [fact.split(":", 1)[1] for fact in used_facts if fact.startswith("actions:")]

        if not actions_in_claim:
            return True, ""  # No actions mentioned is acceptable

        # All actions should be in the canonical experience
        canonical_actions = set(canonical_experience.get("actions", []))
        for action in actions_in_claim:
            if action not in canonical_actions:
                return False, f"Action '{action}' not found in canonical experience"

        return True, ""

    def _check_methods_have_evidence(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 5: Methods have evidence."""
        used_facts = bullet_claim.get("used_facts", [])
        methods_in_claim = [fact.split(":", 1)[1] for fact in used_facts if fact.startswith("methods:")]

        if not methods_in_claim:
            return True, ""

        canonical_methods = set(canonical_experience.get("methods", []))
        for method in methods_in_claim:
            if method not in canonical_methods:
                return False, f"Method '{method}' not found in canonical experience"

        return True, ""

    def _check_tools_have_evidence(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 6: Tools have evidence."""
        used_facts = bullet_claim.get("used_facts", [])
        tools_in_claim = [fact.split(":", 1)[1] for fact in used_facts if fact.startswith("tools:")]

        if not tools_in_claim:
            return True, ""

        canonical_tools = set(canonical_experience.get("tools", []))
        for tool in tools_in_claim:
            if tool not in canonical_tools:
                return False, f"Tool '{tool}' not found in canonical experience"

        return True, ""

    def _check_numbers_match_exactly(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 7: Numbers match exactly."""
        wording = bullet_claim.get("wording", "")
        scope = canonical_experience.get("scope", {})

        # Extract numbers from wording
        wording_numbers = re.findall(r'\d+', wording)

        if not wording_numbers:
            return True, ""

        if not scope:
            return False, "Numbers in claim but no scope defined in canonical experience"

        # Check if all numbers appear in scope values
        scope_values = " ".join(str(v) for v in scope.values())
        scope_numbers = re.findall(r'\d+', scope_values)

        for num in wording_numbers:
            if num not in scope_numbers:
                return False, f"Number '{num}' in claim not found in canonical experience scope"

        return True, ""

    def _check_outcomes_have_evidence(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 8: Outcomes have evidence."""
        used_facts = bullet_claim.get("used_facts", [])
        outcomes_in_claim = [fact.split(":", 1)[1] for fact in used_facts if fact.startswith("outcomes:")]

        if not outcomes_in_claim:
            return True, ""

        canonical_outcomes = set(canonical_experience.get("outcomes", []))
        for outcome in outcomes_in_claim:
            if outcome not in canonical_outcomes:
                return False, f"Outcome '{outcome}' not found in canonical experience"

        return True, ""

    def _check_responsibility_not_upgraded(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 9: Responsibility level not upgraded."""
        claim_level = bullet_claim.get("responsibility_level")
        canonical_level = canonical_experience.get("role", {}).get("responsibility_level")

        if claim_level != canonical_level:
            return False, f"Responsibility level mismatch: claim={claim_level}, canonical={canonical_level}"

        # Also check wording for responsibility upgrade indicators
        wording = bullet_claim.get("wording", "")
        responsibility_level = canonical_level

        # Define responsibility indicators by level (conservative mapping)
        level_indicators = {
            "participated": ["参与", "协助", "support", "assist", "participate"],
            "owned_component": ["负责", "完成", "own", "responsible for"],
            "led_delivery": ["主导", "协调", "lead", "coordinate"],
            "project_owner": ["管理", "overall responsibility", "manage"],
        }

        allowed_indicators = level_indicators.get(responsibility_level, [])
        higher_indicators = []

        # Collect indicators for higher levels
        level_order = ["participated", "owned_component", "led_delivery", "project_owner"]
        current_idx = level_order.index(responsibility_level) if responsibility_level in level_order else -1

        if current_idx >= 0:
            for higher_level in level_order[current_idx + 1:]:
                higher_indicators.extend(level_indicators.get(higher_level, []))

        # Check for higher level indicators in wording
        for indicator in higher_indicators:
            if indicator in wording:
                return False, f"Word contains higher responsibility indicator: '{indicator}'"

        return True, ""

    def _check_no_forbidden_expressions(self, bullet_claim: Dict[str, Any], role_pack: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 10: No forbidden role pack expressions."""
        wording = bullet_claim.get("wording", "")
        forbidden_claims = role_pack.get("forbidden_claims", [])

        for forbidden in forbidden_claims:
            if forbidden in wording:
                return False, f"Contains forbidden expression: '{forbidden}'"

        return True, ""

    def _check_role_value_not_disguised_as_outcome(self, bullet_claim: Dict[str, Any], role_pack: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 11: Role value not disguised as factual outcome."""
        wording = bullet_claim.get("wording", "")
        value_mappings = role_pack.get("value_mappings", {})
        used_facts = bullet_claim.get("used_facts", [])

        # Check if wording contains value mapping phrases
        for domain, mappings in value_mappings.items():
            for mapping_phrase in mappings:
                if mapping_phrase in wording:
                    # If there are actual used facts (actions, methods, etc.),
                    # then the value phrase is likely being used appropriately
                    # as part of standard phrasing, not disguised as a fake outcome
                    has_actual_facts = any(
                        fact.startswith(('actions:', 'methods:', 'tools:', 'objects:'))
                        for fact in used_facts
                    )

                    if not has_actual_facts:
                        # No actual facts used, but value phrase present - suspicious
                        return False, f"Role value phrase '{mapping_phrase}' used without actual factual basis"

        return True, ""

    def _check_user_edits_no_unconfirmed_facts(self, bullet_claim: Dict[str, Any], canonical_experience: Dict[str, Any]) -> Tuple[bool, str]:
        """Check 12: User edits don't introduce unconfirmed facts."""
        # If user_disposition is None or "accepted", no edit occurred
        if bullet_claim.get("user_disposition") in [None, "accepted"]:
            return True, ""

        # If user edited, we need to ensure they didn't add unconfirmed facts
        if bullet_claim.get("user_disposition") == "edited":
            # This is complex to verify perfectly, but we can check:
            # 1. All used_facts should still map to canonical experience
            # 2. Wording shouldn't contain obviously new elements

            # Re-run the used facts check
            used_facts_check = self._check_used_facts_confirmed(bullet_claim, canonical_experience)
            if not used_facts_check[0]:
                return False, f"User edit introduced unconfirmed facts: {used_facts_check[1]}"

            # Check for obvious new elements like numbers not in scope
            numbers_check = self._check_numbers_match_exactly(bullet_claim, canonical_experience)
            if not numbers_check[0]:
                return False, f"User edit introduced unconfirmed numbers: {numbers_check[1]}"

        return True, ""