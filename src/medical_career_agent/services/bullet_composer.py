from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .resume_translation import TARGET_PROFILES


@dataclass(frozen=True)
class BulletClaim:
    """A single resume bullet claim with full traceability."""
    claim_id: str
    experience_id: str
    role_pack: str
    wording: str
    used_facts: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    responsibility_level: str
    omitted_unknowns: Tuple[str, ...]
    risk_flags: Tuple[str, ...]
    verification_status: str = "candidate"
    user_disposition: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "bullet-claim-v1",
            "claim_id": self.claim_id,
            "experience_id": self.experience_id,
            "role_pack": self.role_pack,
            "wording": self.wording,
            "used_facts": list(self.used_facts),
            "evidence_ids": list(self.evidence_ids),
            "responsibility_level": self.responsibility_level,
            "omitted_unknowns": list(self.omitted_unknowns),
            "risk_flags": list(self.risk_flags),
            "verification_status": self.verification_status,
            "user_disposition": self.user_disposition,
        }


class BulletComposerService:
    """Converts Canonical Experience and Role Pack into 1-3 Bullet Claims.

    This service respects the authenticity boundary by:
    - Only using confirmed facts from canonical experience
    - Not inventing new numbers, methods, tools, outcomes, or responsibilities
    - Preserving original evidence references
    - Using role-specific patterns without upgrading responsibility levels
    - Generating multiple candidates that only vary in phrasing, order, and role perspective
    """

    def __init__(self, role_packs_dir: str | Path | None = None):
        self.role_packs_dir = Path(role_packs_dir) if role_packs_dir else Path(__file__).parent.parent.parent.parent / "data" / "role-packs"

    def compose_bullets(
        self,
        *,
        canonical_experience: Dict[str, Any],
        role_pack_name: str,
    ) -> List[BulletClaim]:
        """Generate 1-3 bullet claims from canonical experience for a specific role pack.

        Args:
            canonical_experience: A validated canonical experience record
            role_pack_name: Name of the role pack (e.g., 'doctoral_v1', 'clinical_research_v1')

        Returns:
            List of 1-3 bullet claims ready for resume use

        Raises:
            ValueError: If inputs are invalid or role pack not found
        """
        # Validate canonical experience
        if canonical_experience.get("schema_version") != "canonical-experience-v1":
            raise ValueError("canonical_experience must use canonical-experience-v1 schema")

        if canonical_experience.get("status") != "user_confirmed":
            raise ValueError("canonical_experience must have status 'user_confirmed'")

        experience_id = canonical_experience.get("experience_id")
        if not experience_id:
            raise ValueError("canonical_experience must have experience_id")

        evidence_ids = tuple(canonical_experience.get("evidence_ids", []))
        if not evidence_ids:
            raise ValueError("canonical_experience must have at least one evidence_id")

        # Load role pack
        role_pack = self._load_role_pack(role_pack_name)

        # Extract facts from canonical experience
        facts = self._extract_facts(canonical_experience)
        responsibility_level = canonical_experience["role"]["responsibility_level"]

        # Generate bullet claims using role pack patterns
        bullets = self._generate_bullets(
            facts=facts,
            responsibility_level=responsibility_level,
            role_pack=role_pack,
            experience_id=experience_id,
            evidence_ids=evidence_ids,
            role_pack_name=role_pack_name,
        )

        # Ensure we have 1-3 bullets
        if len(bullets) == 0:
            # Fallback: create at least one basic bullet
            bullets = [self._create_fallback_bullet(
                facts=facts,
                responsibility_level=responsibility_level,
                role_pack=role_pack,
                experience_id=experience_id,
                evidence_ids=evidence_ids,
                role_pack_name=role_pack_name,
            )]

        # Limit to maximum 3 bullets
        bullets = bullets[:3]

        return bullets

    def _load_role_pack(self, role_pack_name: str) -> Dict[str, Any]:
        """Load role pack configuration from JSON file."""
        role_pack_path = self.role_packs_dir / f"{role_pack_name}.json"
        if not role_pack_path.exists():
            raise ValueError(f"Role pack '{role_pack_name}' not found at {role_pack_path}")

        try:
            return json.loads(role_pack_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(f"Failed to load role pack '{role_pack_name}': {e}")

    def _extract_facts(self, canonical_experience: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract all factual elements from canonical experience."""
        facts = {}

        # Extract all array fields that contain facts
        array_fields = [
            "actions", "methods", "tools", "objects", "collaboration",
            "artifacts", "outcomes"
        ]

        for field in array_fields:
            facts[field] = canonical_experience.get(field, [])

        # Extract context and role info
        facts["context"] = canonical_experience.get("context", {})
        facts["role"] = canonical_experience.get("role", {})
        facts["scope"] = canonical_experience.get("scope", {})
        facts["unknowns"] = canonical_experience.get("unknowns", [])

        return facts

    def _generate_bullets(
        self,
        facts: Dict[str, Any],
        responsibility_level: str,
        role_pack: Dict[str, Any],
        experience_id: str,
        evidence_ids: Tuple[str, ...],
        role_pack_name: str,
    ) -> List[BulletClaim]:
        """Generate bullet claims using role pack patterns and facts."""
        bullets = []
        sentence_patterns = role_pack.get("sentence_patterns", [])
        allowed_verbs = role_pack.get("allowed_verbs", [])
        restricted_verbs = role_pack.get("restricted_verbs", [])
        forbidden_claims = role_pack.get("forbidden_claims", [])

        # Get responsibility verb based on level and role pack constraints
        responsibility_verb = self._get_responsibility_verb(responsibility_level, allowed_verbs, restricted_verbs)

        # Generate bullets from each pattern
        for pattern in sentence_patterns:
            try:
                wording = self._fill_pattern(
                    pattern=pattern,
                    facts=facts,
                    responsibility_verb=responsibility_verb,
                    role_pack=role_pack,
                )

                if wording and self._is_valid_claim(wording, forbidden_claims):
                    used_facts = self._extract_used_facts(wording, facts)
                    risk_flags = self._assess_risks(wording, facts, responsibility_level, role_pack)

                    claim_id = f"claim_{uuid4().hex[:8]}"
                    bullet = BulletClaim(
                        claim_id=claim_id,
                        experience_id=experience_id,
                        role_pack=role_pack_name,
                        wording=wording,
                        used_facts=tuple(used_facts),
                        evidence_ids=evidence_ids,
                        responsibility_level=responsibility_level,
                        omitted_unknowns=tuple(facts.get("unknowns", [])),
                        risk_flags=tuple(risk_flags),
                    )
                    bullets.append(bullet)

                    # Stop if we have enough bullets
                    if len(bullets) >= 3:
                        break

            except Exception:
                # Skip invalid patterns silently
                continue

        return bullets

    def _get_responsibility_verb(
        self,
        responsibility_level: str,
        allowed_verbs: List[str],
        restricted_verbs: List[str]
    ) -> str:
        """Get appropriate verb based on responsibility level and role pack constraints."""
        verb_mapping = {
            "participated": ["参与", "协助"],
            "owned_component": ["负责", "完成"],
            "led_delivery": ["主导", "领导"],
            "project_owner": ["负责", "管理"],
            "unknown": ["参与", "协助"],
        }

        candidate_verbs = verb_mapping.get(responsibility_level, ["参与"])

        # Filter by allowed verbs
        if allowed_verbs:
            candidate_verbs = [v for v in candidate_verbs if v in allowed_verbs]

        # Remove restricted verbs
        if restricted_verbs:
            candidate_verbs = [v for v in candidate_verbs if v not in restricted_verbs]

        # Return first available verb, or default
        return candidate_verbs[0] if candidate_verbs else "参与"

    def _fill_pattern(
        self,
        pattern: str,
        facts: Dict[str, Any],
        responsibility_verb: str,
        role_pack: Dict[str, Any],
    ) -> Optional[str]:
        """Fill sentence pattern with actual facts."""
        # Replace placeholders with actual values
        result = pattern

        # Handle responsibility placeholder
        if "{responsibility}" in result:
            result = result.replace("{responsibility}", responsibility_verb)

        # Handle action placeholders
        actions = facts.get("actions", [])
        if actions and "{action}" in result:
            # Use preferred actions from role pack if available
            preferred_actions = role_pack.get("preferred_actions", [])
            if preferred_actions:
                # Find intersection of preferred and available actions
                available_preferred = [a for a in preferred_actions if a in actions]
                action_to_use = available_preferred[0] if available_preferred else actions[0]
            else:
                action_to_use = actions[0]

            # Map action to Chinese if needed (simplified mapping)
            action_mapping = {
                "design": "设计",
                "implement": "实施",
                "analyze": "分析",
                "interpret": "解释",
                "synthesize": "综合",
                "validate": "验证",
                "execute": "执行",
                "support": "支持",
                "assist": "协助",
                "contribute": "贡献",
                "participate": "参与",
                "collect_data": "数据收集",
                "screen_patients": "患者筛选",
                "retrieve_literature": "文献检索",
                "screen_studies": "研究筛选",
                "perform_experiments": "实验操作",
                "collect_samples": "样本收集",
                "analyze_data": "数据分析",
                "validate_results": "结果验证",
                "retrieve_guidelines": "指南检索",
                "summarize_evidence": "证据总结",
            }
            action_chinese = action_mapping.get(action_to_use, action_to_use)
            result = result.replace("{action}", action_chinese)

        # Handle object placeholders
        objects = facts.get("objects", [])
        if objects and "{object}" in result:
            object_mapping = {
                "clinical_studies": "临床研究",
                "medical_literature": "医学文献",
                "clinical_data": "临床数据",
                "research_outcomes": "研究结果",
                "cell_samples": "细胞样本",
                "protein_extracts": "蛋白提取物",
                "patient_records": "患者记录",
                "clinical_variables": "临床变量",
                "trial_data": "试验数据",
                "clinical_outcomes": "临床结局",
                "clinical_guidelines": "临床指南",
                "medical_evidence": "医学证据",
            }
            object_to_use = objects[0]
            object_chinese = object_mapping.get(object_to_use, object_to_use)
            result = result.replace("{object}", object_chinese)

        # Handle method placeholders
        methods = facts.get("methods", [])
        if methods and "{method}" in result:
            method_mapping = {
                "systematic_review": "系统综述",
                "meta_analysis": "Meta分析",
                "statistical_analysis": "统计分析",
                "regression_modeling": "回归建模",
                "pcr": "PCR",
                "western_blot": "Western Blot",
                "cohort_study": "队列研究",
                "data_collection": "数据收集",
                "quality_control": "质量控制",
                "evidence_synthesis": "证据综合",
            }
            method_to_use = methods[0]
            method_chinese = method_mapping.get(method_to_use, method_to_use)
            result = result.replace("{method}", method_chinese)

        # Handle scope placeholders
        scope = facts.get("scope", {})
        if scope and "{scope}" in result:
            scope_str = "、".join([f"{k}:{v}" for k, v in scope.items()])
            result = result.replace("{scope}", scope_str)

        # Handle outcome placeholders
        outcomes = facts.get("outcomes", [])
        if outcomes and "{outcome}" in result:
            result = result.replace("{outcome}", outcomes[0])

        # Handle constraint placeholders (from scope)
        if "{constraint}" in result and scope:
            constraint_str = "在" + "、".join(scope.values()) + "条件下"
            result = result.replace("{constraint}", constraint_str)

        # Handle value placeholders (from role pack value mappings)
        if "{value}" in result:
            context = facts.get("context", {})
            domain = context.get("domain", "")
            value_mappings = role_pack.get("value_mappings", {})
            if domain in value_mappings:
                value_str = value_mappings[domain][0]  # Use first part of mapping
                result = result.replace("{value}", value_str)
            else:
                result = result.replace("{value}", "相关工作")

        # Handle purpose placeholders
        if "{purpose}" in result:
            outcomes = facts.get("outcomes", [])
            if outcomes:
                result = result.replace("{purpose}", f"以{outcomes[0]}")
            else:
                result = result.replace("{purpose}", "以支持相关研究")

        # Clean up any remaining placeholders
        if "{" in result and "}" in result:
            return None  # Incomplete pattern filling

        return result.strip()

    def _is_valid_claim(self, wording: str, forbidden_claims: List[str]) -> bool:
        """Check if claim violates any forbidden patterns."""
        if not wording:
            return False

        # Check against forbidden claims
        for forbidden in forbidden_claims:
            if forbidden in wording:
                return False

        # Basic validation: should not contain unconfirmed elements
        # Should be a reasonable length
        if len(wording) < 10 or len(wording) > 200:
            return False

        return True

    def _extract_used_facts(self, wording: str, facts: Dict[str, Any]) -> List[str]:
        """Extract which facts were actually used in the wording."""
        used_facts = []

        # Check which fact categories appear in the wording
        for category, items in facts.items():
            if isinstance(items, list):
                for item in items:
                    if str(item) in wording:
                        used_facts.append(f"{category}:{item}")
            elif isinstance(items, dict):
                for key, value in items.items():
                    if str(value) in wording:
                        used_facts.append(f"{category}.{key}:{value}")

        return used_facts

    def _assess_risks(
        self,
        wording: str,
        facts: Dict[str, Any],
        responsibility_level: str,
        role_pack: Dict[str, Any]
    ) -> List[str]:
        """Assess potential risks in the bullet claim."""
        risks = []

        # Check for responsibility level escalation
        responsibility_verb = self._get_responsibility_verb(
            responsibility_level,
            role_pack.get("allowed_verbs", []),
            role_pack.get("restricted_verbs", [])
        )

        # Risk: wording contains verbs stronger than allowed
        restricted_verbs = role_pack.get("restricted_verbs", [])
        for verb in restricted_verbs:
            if verb in wording:
                risks.append(f"contains restricted verb: {verb}")

        # Risk: wording implies higher responsibility than actual
        high_responsibility_indicators = ["独立", "创新", "领导", "管理", "负责整体"]
        actual_level_indicators = {
            "participated": ["参与", "协助"],
            "owned_component": ["负责", "完成"],
            "led_delivery": ["主导", "协调"],
            "project_owner": ["负责", "管理"],
        }

        actual_indicators = actual_level_indicators.get(responsibility_level, [])
        for indicator in high_responsibility_indicators:
            if indicator in wording and indicator not in actual_indicators:
                risks.append(f"implies higher responsibility: {indicator}")

        # Risk: contains unconfirmed facts
        unknowns = facts.get("unknowns", [])
        for unknown in unknowns:
            if unknown in wording:
                risks.append(f"includes unknown fact: {unknown}")

        return risks

    def _create_fallback_bullet(
        self,
        facts: Dict[str, Any],
        responsibility_level: str,
        role_pack: Dict[str, Any],
        experience_id: str,
        evidence_ids: Tuple[str, ...],
        role_pack_name: str,
    ) -> BulletClaim:
        """Create a basic fallback bullet when patterns fail."""
        # Simple construction: [responsibility] [action] [object]
        responsibility_verb = self._get_responsibility_verb(
            responsibility_level,
            role_pack.get("allowed_verbs", []),
            role_pack.get("restricted_verbs", [])
        )

        actions = facts.get("actions", [])
        objects = facts.get("objects", [])

        action_str = actions[0] if actions else "相关工作"
        object_str = objects[0] if objects else "项目"

        # Simple mapping for fallback
        action_mapping = {
            "design": "设计", "implement": "实施", "analyze": "分析", "interpret": "解释",
            "synthesize": "综合", "validate": "验证", "execute": "执行", "support": "支持",
            "assist": "协助", "contribute": "贡献", "participate": "参与",
            "collect_data": "数据收集", "screen_patients": "患者筛选",
            "retrieve_literature": "文献检索", "screen_studies": "研究筛选",
            "perform_experiments": "实验操作", "collect_samples": "样本收集",
            "analyze_data": "数据分析", "validate_results": "结果验证",
            "retrieve_guidelines": "指南检索", "summarize_evidence": "证据总结",
        }
        object_mapping = {
            "clinical_studies": "临床研究", "medical_literature": "医学文献",
            "clinical_data": "临床数据", "research_outcomes": "研究结果",
            "cell_samples": "细胞样本", "protein_extracts": "蛋白提取物",
            "patient_records": "患者记录", "clinical_variables": "临床变量",
            "trial_data": "试验数据", "clinical_outcomes": "临床结局",
            "clinical_guidelines": "临床指南", "medical_evidence": "医学证据",
        }

        action_chinese = action_mapping.get(action_str, action_str)
        object_chinese = object_mapping.get(object_str, object_str)

        wording = f"{responsibility_verb}{action_chinese}{object_chinese}，支持相关研究工作。"

        claim_id = f"claim_{uuid4().hex[:8]}"
        used_facts = [f"actions:{action_str}", f"objects:{object_str}"] if actions and objects else []
        risk_flags = ["fallback_construction"]

        return BulletClaim(
            claim_id=claim_id,
            experience_id=experience_id,
            role_pack=role_pack_name,
            wording=wording,
            used_facts=tuple(used_facts),
            evidence_ids=evidence_ids,
            responsibility_level=responsibility_level,
            omitted_unknowns=tuple(facts.get("unknowns", [])),
            risk_flags=tuple(risk_flags),
        )