"""v2 activity/responsibility validation and read compatibility helpers."""
from __future__ import annotations

from typing import Any

ACTIVITY_COMPONENTS = ("actions", "methods", "tools", "techniques", "objects", "artifacts")


def normalise_activity_responsibility(experience: dict[str, Any]) -> dict[str, Any]:
    """Return a read model without fabricating task-level assertions for v1."""
    if experience.get("schema_version") == "canonical-experience-v2":
        return {"source_schema_version": "canonical-experience-v2", "activities": experience.get("activities", []), "task_responsibilities": experience.get("task_responsibilities", []), "responsibility_resolution": "confirmed"}
    return {"source_schema_version": experience.get("schema_version"), "activities": [], "task_responsibilities": [], "responsibility_resolution": "legacy_project_level_only"}


def validate_confirmed_activities(*, activities: list[dict[str, Any]], responsibilities: list[dict[str, Any]], facts: dict[str, Any], evidence_ids: set[str], fact_evidence_map: dict[str, list[str]], activity_evidence_overrides: dict[str, dict[str, list[str]]] | None = None) -> list[str]:
    """Validate atomic combinations against supplied evidence, never activity.label."""
    errors: list[str] = []
    ids: set[str] = set()
    for activity in activities:
        activity_id = str(activity.get("activity_id", ""))
        if not activity_id or activity_id in ids:
            errors.append("activities must have unique non-empty activity_id")
            continue
        ids.add(activity_id)
        if activity.get("status") != "user_confirmed":
            errors.append(f"activity {activity_id} must be user_confirmed")
        components = activity.get("components", {})
        component_values: list[str] = []
        if not isinstance(components, dict):
            errors.append(f"activity {activity_id} components must be an object")
            continue
        for category in ACTIVITY_COMPONENTS:
            values = components.get(category, [])
            if not isinstance(values, list):
                errors.append(f"activity {activity_id} {category} must be a list")
                continue
            for value in values:
                if value not in facts.get(category, []):
                    errors.append(f"activity {activity_id} component {category}:{value} is not a confirmed fact")
                component_values.append(str(value))
        if not component_values:
            errors.append(f"activity {activity_id} must contain at least one component")
        activity_evidence = set(activity.get("evidence_ids", []))
        if not activity_evidence or not activity_evidence.issubset(evidence_ids):
            errors.append(f"activity {activity_id} must cite current experience evidence")
        # Each component category must have an evidence mapping covered by the
        # activity.  This checks the full combination; activity.label is ignored.
        for category in ACTIVITY_COMPONENTS:
            if components.get(category):
                required = set((activity_evidence_overrides or {}).get(activity_id, {}).get(category, fact_evidence_map.get(category, [])))
                if not required or not required.issubset(activity_evidence):
                    errors.append(f"activity {activity_id} evidence does not support all {category} components")
    seen_activity: set[str] = set()
    for responsibility in responsibilities:
        activity_id = str(responsibility.get("activity_id", ""))
        if activity_id not in ids:
            errors.append(f"responsibility references unknown activity {activity_id}")
        if activity_id in seen_activity:
            errors.append(f"activity {activity_id} may have only one current confirmed responsibility")
        seen_activity.add(activity_id)
        if responsibility.get("ownership_level") not in {"contributed", "owned_component", "led_delivery", "accountable"}:
            errors.append(f"responsibility for {activity_id} has invalid ownership_level")
        if responsibility.get("execution_mode") not in {"supervised", "independent", "shared"}:
            errors.append(f"responsibility for {activity_id} has invalid execution_mode")
        scope = responsibility.get("scope", {})
        if not isinstance(scope, dict) or scope.get("coverage") not in {"full", "partial"}:
            errors.append(f"responsibility for {activity_id} has invalid scope")
        cited = set(responsibility.get("evidence_ids", []))
        if not cited or not cited.issubset(evidence_ids):
            errors.append(f"responsibility for {activity_id} must cite current experience evidence")
    return errors
