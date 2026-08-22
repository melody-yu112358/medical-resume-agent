from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional
from uuid import uuid4

from ..adapters.openai_compatible_model_gateway import ModelGatewayError


@dataclass(frozen=True)
class ConfirmationResult:
    """Result of the confirmation process."""

    canonical_experience: Optional[dict[str, Any]]
    confirmation_status: dict[str, Any]
    fact_evidence_map: dict[str, list[str]]
    invalidation: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "canonical_experience": self.canonical_experience,
            "confirmation_status": self.confirmation_status,
            "fact_evidence_map": self.fact_evidence_map,
        }
        if self.invalidation:
            result["invalidation"] = self.invalidation
        return result


class ConfirmationGateService:
    """Handles user confirmation of experience drafts and generates canonical experiences."""

    def __init__(self):
        self._next_evidence_id = 1

    def confirm_experience(
        self,
        *,
        experience_draft: dict[str, Any],
        user_actions: dict[str, Any],
        evidence_records: list[dict[str, Any]],
        previous_experience_id: Optional[str] = None,
    ) -> ConfirmationResult:
        """Confirm, modify, or reject an experience draft based on user actions."""

        disposition = user_actions.get("disposition", "accept")

        if disposition == "reject":
            return self._handle_rejection(evidence_records, previous_experience_id)

        # Handle accept or edit dispositions
        confirmed_facts = user_actions.get("confirmed_facts", [])
        modified_facts = user_actions.get("modified_facts", {})
        new_evidence_text = user_actions.get("new_evidence", "")

        # Validate that we have evidence records
        if not evidence_records:
            return ConfirmationResult(
                canonical_experience=None,
                confirmation_status={
                    "status": "needs_more_info",
                    "missing_confirmations": ["evidence_records"],
                    "validation_errors": ["No evidence records provided"]
                },
                fact_evidence_map={}
            )

        # Get the original extracted facts
        extracted_facts = experience_draft.get("extracted_facts", {})

        # Validate responsibility level upgrade BEFORE applying modifications
        original_responsibility = extracted_facts.get("role", {}).get("responsibility_level", "participated")
        new_responsibility = original_responsibility

        if "role.responsibility_level" in modified_facts:
            new_responsibility = modified_facts["role.responsibility_level"]
        elif "role" in modified_facts and isinstance(modified_facts["role"], dict):
            new_responsibility = modified_facts["role"].get("responsibility_level", original_responsibility)

        # Check if responsibility level needs explicit confirmation for upgrades
        if (new_responsibility != original_responsibility and
            new_responsibility in ["owned_component", "led_delivery", "project_owner"] and
            not new_evidence_text.strip()):  # Check if new evidence is actually provided
            return ConfirmationResult(
                canonical_experience=None,
                confirmation_status={
                    "status": "needs_more_info",
                    "missing_confirmations": ["responsibility_level_evidence"],
                    "validation_errors": [f"Upgrading responsibility level to {new_responsibility} requires new evidence"]
                },
                fact_evidence_map={}
            )

        # Create fact-evidence mapping for original facts
        fact_evidence_map = self._create_initial_fact_evidence_map(extracted_facts, evidence_records)

        # Handle modifications if any
        if modified_facts or new_evidence_text.strip():
            if new_evidence_text.strip():
                # Create new evidence record for user modifications
                new_evidence_id = f"ev_{self._next_evidence_id:03d}"
                self._next_evidence_id += 1

                new_evidence_record = {
                    "evidence_id": new_evidence_id,
                    "source_text": new_evidence_text,
                    "status": "confirmed"
                }
                evidence_records.append(new_evidence_record)

                # Update facts with modifications and map to new evidence
                updated_facts, updated_map = self._apply_modifications(
                    extracted_facts, modified_facts, new_evidence_id
                )
                extracted_facts = updated_facts
                fact_evidence_map.update(updated_map)
            else:
                # Apply modifications without new evidence (should only be safe modifications)
                updated_facts, updated_map = self._apply_modifications(
                    extracted_facts, modified_facts, evidence_records[0]["evidence_id"]
                )
                extracted_facts = updated_facts
                fact_evidence_map.update(updated_map)

        # Validate the extracted facts structure before building canonical experience
        fact_validation_errors = self._validate_extracted_facts(extracted_facts)
        if fact_validation_errors:
            return ConfirmationResult(
                canonical_experience=None,
                confirmation_status={
                    "status": "needs_more_info",
                    "missing_confirmations": [],
                    "validation_errors": fact_validation_errors
                },
                fact_evidence_map=fact_evidence_map
            )

        # Create canonical experience
        canonical_experience = self._build_canonical_experience(
            extracted_facts, evidence_records, previous_experience_id
        )

        # Validate canonical experience against schema requirements
        validation_errors = self._validate_canonical_experience(canonical_experience)
        if validation_errors:
            return ConfirmationResult(
                canonical_experience=None,
                confirmation_status={
                    "status": "needs_more_info",
                    "missing_confirmations": [],
                    "validation_errors": validation_errors
                },
                fact_evidence_map=fact_evidence_map
            )

        # Determine final status
        status = "ready" if disposition == "accept" else "edited"

        # Create invalidation event if there was a previous experience
        invalidation = None
        if previous_experience_id:
            invalidation = {
                "previous_experience_id": previous_experience_id,
                "reason": "confirmed_fact_changed",
                "invalidate_related_claims": True
            }

        return ConfirmationResult(
            canonical_experience=canonical_experience,
            confirmation_status={"status": status},
            fact_evidence_map=fact_evidence_map,
            invalidation=invalidation
        )

    def _handle_rejection(
        self,
        evidence_records: list[dict[str, Any]],
        previous_experience_id: Optional[str]
    ) -> ConfirmationResult:
        """Handle rejection of the experience draft."""
        # Create a rejected canonical experience
        if evidence_records:
            evidence_ids = [record["evidence_id"] for record in evidence_records]
        else:
            evidence_ids = []

        rejected_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": f"exp_{uuid4().hex[:8]}",
            "evidence_ids": evidence_ids,
            "context": {"domain": "other", "setting": "other", "topic": None},
            "role": {"title": None, "responsibility_level": "unknown"},
            "actions": [],
            "methods": [],
            "tools": [],
            "objects": [],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
            "status": "rejected"
        }

        # Create invalidation event if there was a previous experience
        invalidation = None
        if previous_experience_id:
            invalidation = {
                "previous_experience_id": previous_experience_id,
                "reason": "user_rejected",
                "invalidate_related_claims": True
            }

        return ConfirmationResult(
            canonical_experience=rejected_experience,
            confirmation_status={"status": "rejected"},
            fact_evidence_map={},
            invalidation=invalidation
        )

    def _create_initial_fact_evidence_map(
        self,
        extracted_facts: dict[str, Any],
        evidence_records: list[dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Create initial fact-evidence mapping for extracted facts."""
        if not evidence_records:
            return {}

        primary_evidence_id = evidence_records[0]["evidence_id"]
        fact_evidence_map = {}

        # Map each fact field to the primary evidence
        for category, items in extracted_facts.items():
            if isinstance(items, dict):
                for subfield, value in items.items():
                    if value is not None and value != "":
                        key = f"{category}.{subfield}"
                        fact_evidence_map[key] = [primary_evidence_id]
            elif isinstance(items, list) and items:
                # For list fields, map the entire category
                fact_evidence_map[category] = [primary_evidence_id]
            elif items is not None and items != "":
                # For scalar fields
                fact_evidence_map[category] = [primary_evidence_id]

        return fact_evidence_map

    def _apply_modifications(
        self,
        original_facts: dict[str, Any],
        modifications: dict[str, Any],
        evidence_id: str
    ) -> tuple[dict[str, Any], dict[str, list[str]]]:
        """Apply user modifications to facts and create mapping for modified fields."""
        updated_facts = {}

        # Deep copy the original facts
        for key, value in original_facts.items():
            if isinstance(value, dict):
                updated_facts[key] = value.copy()
            elif isinstance(value, list):
                updated_facts[key] = value[:]
            else:
                updated_facts[key] = value

        modification_map = {}

        for field_path, new_value in modifications.items():
            # Handle nested fields like "role.responsibility_level"
            if "." in field_path:
                category, subfield = field_path.split(".", 1)
                if category not in updated_facts:
                    updated_facts[category] = {}
                if isinstance(updated_facts[category], dict):
                    updated_facts[category][subfield] = new_value
                    modification_map[field_path] = [evidence_id]
            else:
                # Handle top-level fields
                updated_facts[field_path] = new_value
                modification_map[field_path] = [evidence_id]

        return updated_facts, modification_map

    def _validate_extracted_facts(self, extracted_facts: dict[str, Any]) -> list[str]:
        """Validate the structure of extracted facts before building canonical experience."""
        errors = []

        # Required top-level categories
        required_categories = ["context", "role"]
        for category in required_categories:
            if category not in extracted_facts:
                errors.append(f"Missing required category: {category}")
            elif not isinstance(extracted_facts[category], dict):
                errors.append(f"Category {category} must be a dictionary")

        # Validate context
        if "context" in extracted_facts:
            context = extracted_facts["context"]
            if "domain" not in context:
                errors.append("Context must contain 'domain'")
            if "setting" not in context:
                errors.append("Context must contain 'setting'")

        # Validate role
        if "role" in extracted_facts:
            role = extracted_facts["role"]
            if "responsibility_level" not in role:
                errors.append("Role must contain 'responsibility_level'")

        return errors

    def _build_canonical_experience(
        self,
        extracted_facts: dict[str, Any],
        evidence_records: list[dict[str, Any]],
        previous_experience_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Build a canonical experience record from confirmed facts."""
        evidence_ids = [record["evidence_id"] for record in evidence_records]

        # Build the canonical experience structure using only what's provided
        # Don't fill in defaults for missing fields - let validation catch them
        canonical = {
            "schema_version": "canonical-experience-v1",
            "experience_id": f"exp_{uuid4().hex[:8]}",
            "evidence_ids": evidence_ids,
            "context": extracted_facts.get("context", {}),
            "role": extracted_facts.get("role", {}),
            "actions": extracted_facts.get("actions", []),
            "methods": extracted_facts.get("methods", []),
            "tools": extracted_facts.get("tools", []),
            "objects": extracted_facts.get("objects", []),
            "collaboration": extracted_facts.get("collaboration", []),
            "artifacts": extracted_facts.get("artifacts", []),
            "outcomes": extracted_facts.get("outcomes", []),
            "scope": extracted_facts.get("scope", {}),
            "unknowns": extracted_facts.get("unknown_items", []),
            "status": "user_confirmed"
        }

        return canonical

    def _validate_canonical_experience(self, canonical: dict[str, Any]) -> list[str]:
        """Validate canonical experience against schema requirements."""
        errors = []

        # Required fields check
        required_fields = [
            "schema_version", "experience_id", "evidence_ids", "context",
            "role", "actions", "methods", "tools", "objects", "collaboration",
            "artifacts", "outcomes", "scope", "unknowns", "status"
        ]

        for field in required_fields:
            if field not in canonical:
                errors.append(f"Missing required field: {field}")

        # Schema version check
        if canonical.get("schema_version") != "canonical-experience-v1":
            errors.append("Invalid schema_version")

        # Evidence IDs check
        if not canonical.get("evidence_ids"):
            errors.append("At least one evidence_id is required")

        # Context validation
        context = canonical.get("context", {})
        if not isinstance(context, dict):
            errors.append("Context must be a dictionary")
        else:
            if "domain" not in context:
                errors.append("Context must contain domain")
            if "setting" not in context:
                errors.append("Context must contain setting")
            if "topic" not in context:
                # Topic can be null, but should exist
                context["topic"] = None

        # Role validation
        role = canonical.get("role", {})
        if not isinstance(role, dict):
            errors.append("Role must be a dictionary")
        else:
            if "responsibility_level" not in role:
                errors.append("Role must contain responsibility_level")
            if "title" not in role:
                role["title"] = None

        # Status validation
        valid_statuses = ["user_confirmed", "rejected", "superseded"]
        if canonical.get("status") not in valid_statuses:
            errors.append(f"Invalid status: {canonical.get('status')}")

        # List field validation
        list_fields = ["actions", "methods", "tools", "objects", "collaboration", "artifacts", "outcomes", "unknowns"]
        for field in list_fields:
            if not isinstance(canonical.get(field, []), list):
                errors.append(f"{field} must be a list")

        # Scope validation
        if not isinstance(canonical.get("scope", {}), dict):
            errors.append("scope must be a dictionary")

        return errors