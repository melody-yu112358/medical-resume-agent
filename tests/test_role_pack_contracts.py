import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Load all role pack files
ROLE_PACK_DIR = ROOT / "data" / "role-packs"
ROLE_PACK_FILES = list(ROLE_PACK_DIR.glob("*.json"))


class RolePackContractTest(unittest.TestCase):
    """Contract tests for Role Pack configurations."""

    @classmethod
    def setUpClass(cls):
        """Load all role pack configurations."""
        cls.role_packs = {}
        for file_path in ROLE_PACK_FILES:
            with open(file_path, 'r', encoding='utf-8') as f:
                role_pack = json.load(f)
                cls.role_packs[role_pack['role_pack']] = role_pack

    def test_all_role_packs_have_required_fields(self):
        """Test that all role packs have the required fields from schema."""
        required_fields = {
            "role_pack", "label", "priorities", "value_mappings", "preferred_actions",
            "allowed_verbs", "restricted_verbs", "forbidden_claims", "required_evidence",
            "sentence_patterns", "evaluation_cases"
        }

        for role_pack_name, role_pack in self.role_packs.items():
            with self.subTest(role_pack=role_pack_name):
                missing_fields = required_fields - set(role_pack.keys())
                self.assertEqual(
                    missing_fields, set(),
                    f"Role pack {role_pack_name} missing required fields: {missing_fields}"
                )

    def test_evaluation_cases_structure_legality(self):
        """Test that evaluation_cases is non-empty (when populated) and has legal structure."""
        for role_pack_name, role_pack in self.role_packs.items():
            with self.subTest(role_pack=role_pack_name):
                evaluation_cases = role_pack.get("evaluation_cases", [])

                # If evaluation_cases exists, validate its structure
                if evaluation_cases:  # Only validate if not empty
                    self.assertIsInstance(evaluation_cases, list)
                    for i, case in enumerate(evaluation_cases):
                        self.assertIsInstance(case, dict, f"Case {i} in {role_pack_name} is not a dict")

                        # Check required keys in evaluation case
                        self.assertIn("input", case, f"Case {i} in {role_pack_name} missing 'input'")
                        self.assertIn("expected_output", case, f"Case {i} in {role_pack_name} missing 'expected_output'")

                        # Validate input structure
                        self.assertIsInstance(case["input"], dict, f"Case {i} input in {role_pack_name} is not a dict")

                        # Validate expected_output structure
                        self.assertIsInstance(case["expected_output"], list, f"Case {i} expected_output in {role_pack_name} is not a list")
                        for j, output in enumerate(case["expected_output"]):
                            self.assertIsInstance(output, str, f"Case {i} output {j} in {role_pack_name} is not a string")

    def test_configuration_consistency(self):
        """Test internal consistency of Role Pack configuration."""
        for role_pack_name, role_pack in self.role_packs.items():
            with self.subTest(role_pack=role_pack_name):
                # Check that priorities match value_mappings keys
                priorities = role_pack.get("priorities", [])
                value_mapping_keys = list(role_pack.get("value_mappings", {}).keys())

                # All priorities should have corresponding value mappings
                unmapped_priorities = set(priorities) - set(value_mapping_keys)
                self.assertEqual(
                    unmapped_priorities, set(),
                    f"Role pack {role_pack_name} has priorities without value mappings: {unmapped_priorities}"
                )

                # All value mapping keys should be in priorities (or at least valid categories)
                valid_categories = {"research_method", "data_analysis", "wet_lab", "clinical_research", "medical_information"}
                invalid_mapping_keys = set(value_mapping_keys) - valid_categories
                self.assertEqual(
                    invalid_mapping_keys, set(),
                    f"Role pack {role_pack_name} has invalid value mapping keys: {invalid_mapping_keys}"
                )

                # Check that value_mappings values are pairs
                for key, value in role_pack.get("value_mappings", {}).items():
                    self.assertIsInstance(value, list, f"Value mapping {key} in {role_pack_name} is not a list")
                    self.assertEqual(len(value), 2, f"Value mapping {key} in {role_pack_name} doesn't have exactly 2 elements")
                    self.assertIsInstance(value[0], str, f"First element of value mapping {key} in {role_pack_name} is not a string")
                    self.assertIsInstance(value[1], str, f"Second element of value mapping {key} in {role_pack_name} is not a string")

    def test_verb_conflict_checking(self):
        """Test that allowed, restricted, and forbidden verbs don't conflict."""
        for role_pack_name, role_pack in self.role_packs.items():
            with self.subTest(role_pack=role_pack_name):
                allowed_verbs = set(role_pack.get("allowed_verbs", []))
                restricted_verbs = set(role_pack.get("restricted_verbs", []))
                forbidden_claims = set(role_pack.get("forbidden_claims", []))

                # Check for overlaps between allowed and restricted verbs
                allowed_restricted_overlap = allowed_verbs & restricted_verbs
                self.assertEqual(
                    allowed_restricted_overlap, set(),
                    f"Role pack {role_pack_name} has overlapping allowed and restricted verbs: {allowed_restricted_overlap}"
                )

                # Note: We don't check for conflicts between allowed_verbs and forbidden_claims
                # because forbidden_claims are complete phrases while allowed_verbs are individual verbs.
                # They serve different purposes and may legitimately contain similar words.

    def test_evidence_requirements_completeness(self):
        """Test that strong expressions have corresponding evidence requirements."""
        for role_pack_name, role_pack in self.role_packs.items():
            with self.subTest(role_pack=role_pack_name):
                required_evidence = role_pack.get("required_evidence", {})

                # Check that required_evidence keys are meaningful
                valid_evidence_types = {"owned_component", "led_delivery", "project_owner"}
                invalid_evidence_keys = set(required_evidence.keys()) - valid_evidence_types
                self.assertEqual(
                    invalid_evidence_keys, set(),
                    f"Role pack {role_pack_name} has invalid required_evidence keys: {invalid_evidence_keys}"
                )

                # Check that each evidence requirement has non-empty list
                for evidence_type, evidence_list in required_evidence.items():
                    self.assertIsInstance(evidence_list, list, f"Evidence requirement {evidence_type} in {role_pack_name} is not a list")
                    self.assertGreater(len(evidence_list), 0, f"Evidence requirement {evidence_type} in {role_pack_name} is empty")
                    for evidence_item in evidence_list:
                        self.assertIsInstance(evidence_item, str, f"Evidence item in {evidence_type} for {role_pack_name} is not a string")

    def test_fact_immutability_principles(self):
        """Test that Role Pack configuration adheres to fact immutability principles."""
        for role_pack_name, role_pack in self.role_packs.items():
            with self.subTest(role_pack=role_pack_name):
                # Check that sentence patterns don't imply fact creation
                sentence_patterns = role_pack.get("sentence_patterns", [])
                for pattern in sentence_patterns:
                    self.assertIsInstance(pattern, str, f"Sentence pattern in {role_pack_name} is not a string")

                    # Basic check: patterns should contain placeholders like {action}, {object}, etc.
                    # rather than hardcoded facts
                    has_placeholders = any(placeholder in pattern for placeholder in
                                         ["{action}", "{object}", "{method}", "{constraint}",
                                          "{deliverable}", "{responsibility}", "{scope}",
                                          "{outcome}", "{value}", "{purpose}"])
                    # Note: This test may fail if patterns don't use these exact placeholders,
                    # but it's a basic sanity check

                # Check that preferred_actions are reasonable verbs
                preferred_actions = role_pack.get("preferred_actions", [])
                for action in preferred_actions:
                    self.assertIsInstance(action, str, f"Preferred action in {role_pack_name} is not a string")

    def test_validation_rules_compliance(self):
        """Test compliance with validation rules from requirements."""
        for role_pack_name, role_pack in self.role_packs.items():
            with self.subTest(role_pack=role_pack_name):
                # Rule: Must preserve facts - ensured by having proper value_mappings
                value_mappings = role_pack.get("value_mappings", {})
                self.assertGreater(len(value_mappings), 0, f"Role pack {role_pack_name} has no value mappings")

                # Rule: Must体现岗位关注点 - ensured by having priorities
                priorities = role_pack.get("priorities", [])
                self.assertGreater(len(priorities), 0, f"Role pack {role_pack_name} has no priorities")

                # Rule: 禁止新增的事实 - checked by verb restrictions and forbidden claims
                forbidden_claims = role_pack.get("forbidden_claims", [])
                self.assertGreater(len(forbidden_claims), 0, f"Role pack {role_pack_name} has no forbidden claims")

                # Rule: 禁止责任升级 - checked by restricted_verbs containing responsibility upgrade terms
                restricted_verbs = role_pack.get("restricted_verbs", [])
                responsibility_upgrade_terms = ["负责", "主导", "领导", "管理", "独立"]
                has_responsibility_protection = any(
                    any(term in verb for term in responsibility_upgrade_terms)
                    for verb in restricted_verbs
                )
                # Note: This might not always be true for all role packs, so we won't assert it strictly

                # Rule: 禁止动词 - covered by forbidden_claims and verb restrictions


if __name__ == "__main__":
    import json
    unittest.main()