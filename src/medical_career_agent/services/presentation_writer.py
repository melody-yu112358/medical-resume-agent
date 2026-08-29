"""Compose a candidate-facing resume sentence from already-audited claims.

This layer is intentionally downstream of ClaimGate.  It never creates facts:
it only chooses wording and grouping for a supplied set of ready atomic claims.
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..ports.repositories import ModelGateway


class PresentationWriterService:
    def __init__(self, model_gateway: ModelGateway | None = None) -> None:
        self.model_gateway = model_gateway

    def compose(self, *, claims: list[dict[str, Any]], canonical: dict[str, Any], target: str | None, preference: str) -> dict[str, Any]:
        candidate, _ = self.compose_with_trace(claims=claims, canonical=canonical, target=target, preference=preference)
        return candidate

    def compose_with_trace(self, *, claims: list[dict[str, Any]], canonical: dict[str, Any], target: str | None, preference: str) -> tuple[dict[str, Any], dict[str, str]]:
        """Return a candidate plus safe runtime status; never retain model text."""
        source_ids = [claim["claim_id"] for claim in claims]
        fallback = self._fallback(claims, canonical, target, preference)
        if not self.model_gateway:
            return fallback, {"called": "false", "status": "not_configured", "validation_status": "not_called"}
        try:
            raw = self.model_gateway.generate(task="resume_presentation_writer", context={
                "instruction": (
                    "Return JSON only. Write one natural Chinese resume bullet from ready atomic claims. "
                    "You may combine claims, but must not add facts, outcomes, numbers, tools, methods, "
                    "or strengthen responsibility. Keep independent and supervised work in separate clauses. "
                    "For each clause, provide the exact source_claim_ids it expresses. "
                    "Never mention ClaimGate, audits, schemas, or internal ids in wording."
                ),
                "target_role": target,
                "writing_preference": preference,
                "ready_claims": claims,
                "canonical_experience": canonical,
                "response_shape": {
                    "wording": "one Chinese resume bullet", "source_claim_ids": source_ids,
                    "clauses": [{"text": "substring from wording", "source_claim_ids": ["claim_id"]}],
                },
            })
            candidate = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I | re.S))
            valid = self.validate(candidate, claims)
            if valid is not None:
                return valid, {"called": "true", "status": "success", "validation_status": "accepted"}
            return fallback, {"called": "true", "status": "success", "validation_status": "rejected"}
        except Exception as exc:
            return fallback, {"called": "true", "status": "error", "validation_status": "not_run", "error": self._safe_error(exc)}

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        message = str(exc).replace("\n", " ").strip()
        return f"{type(exc).__name__}: {message[:160]}" if message else type(exc).__name__

    def validate(self, candidate: Any, claims: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("wording"), str):
            return None
        wording = candidate["wording"].strip()
        ready = {claim["claim_id"]: claim for claim in claims}
        source_ids = candidate.get("source_claim_ids")
        clauses = candidate.get("clauses")
        if not wording or not isinstance(source_ids, list) or not source_ids or not set(source_ids).issubset(ready):
            return None
        if not isinstance(clauses, list) or not clauses:
            return None
        traced: set[str] = set()
        for clause in clauses:
            if not isinstance(clause, dict) or not isinstance(clause.get("text"), str) or clause["text"] not in wording:
                return None
            ids = clause.get("source_claim_ids")
            if not isinstance(ids, list) or not ids or not set(ids).issubset(set(source_ids)):
                return None
            traced.update(ids)
            # A clause must preserve the boundary of every source claim it names.
            for claim_id in ids:
                source = ready[claim_id]
                text = clause["text"]
                activity = source.get("activity_id")
                if activity and "supervised" in source.get("wording", ""):
                    # Old records may not carry an explicit wording marker; do
                    # not use this branch as the security decision.
                    continue
                if "在指导下" in source.get("wording", "") and "指导" not in text:
                    return None
                if source.get("wording", "").startswith("独立") and "独立" not in text:
                    return None
        if traced != set(source_ids):
            return None
        evidence_ids = sorted({evidence_id for claim_id in source_ids for evidence_id in ready[claim_id].get("evidence_ids", [])})
        activity_ids = sorted({activity_id for claim_id in source_ids for activity_id in ready[claim_id].get("dependency_refs", {}).get("activity_ids", [])})
        return {"wording": wording, "source_claim_ids": source_ids, "clauses": clauses,
                "activity_ids": activity_ids, "evidence_ids": evidence_ids, "status": "ready"}

    @staticmethod
    def _fallback(claims: list[dict[str, Any]], canonical: dict[str, Any], target: str | None, preference: str) -> dict[str, Any]:
        activities = {item.get("activity_id"): item for item in canonical.get("activities", [])}
        grouped: dict[str, list[dict[str, Any]]] = {"independent": [], "supervised": [], "other": []}
        for claim in claims:
            wording = claim.get("wording", "")
            bucket = "supervised" if "指导" in wording else "independent" if wording.startswith("独立") else "other"
            grouped[bucket].append(claim)

        def rendered(items: list[dict[str, Any]]) -> str:
            labels: list[str] = []
            for claim in items:
                activity = activities.get(claim.get("activity_id"), {})
                components = activity.get("components", {})
                action = (components.get("actions") or [""])[0]
                if action == "retrieve_literature": labels.append("PubMed 文献检索")
                elif action == "screen_studies": labels.append("研究筛选")
                elif action == "perform_analysis": labels.append("使用 R 进行 Meta 分析数据分析")
                else: labels.append(claim.get("wording", "").rstrip("。"))
            return "及".join(labels)

        clauses: list[dict[str, Any]] = []
        if grouped["independent"]:
            text = "独立完成" + rendered(grouped["independent"])
            clauses.append({"text": text, "source_claim_ids": [claim["claim_id"] for claim in grouped["independent"]]})
        if grouped["supervised"]:
            text = "并在导师指导下" + rendered(grouped["supervised"])
            clauses.append({"text": text, "source_claim_ids": [claim["claim_id"] for claim in grouped["supervised"]]})
        if grouped["other"]:
            text = "参与" + rendered(grouped["other"])
            clauses.append({"text": text, "source_claim_ids": [claim["claim_id"] for claim in grouped["other"]]})
        wording = "参与 Meta 分析项目，" + "，".join(clause["text"] for clause in clauses) + "。"
        source_ids = [claim["claim_id"] for claim in claims]
        return {"wording": wording, "source_claim_ids": source_ids, "clauses": clauses,
                "activity_ids": sorted({activity_id for claim in claims for activity_id in claim.get("dependency_refs", {}).get("activity_ids", [])}),
                "evidence_ids": sorted({evidence_id for claim in claims for evidence_id in claim.get("evidence_ids", [])}), "status": "ready"}
