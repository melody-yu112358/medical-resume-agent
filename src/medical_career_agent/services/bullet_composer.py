from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .resume_translation import TARGET_PROFILES
from .resume_vocabulary import FACT_LABELS


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


@dataclass(frozen=True)
class BulletClaimV2:
    """A claim whose responsibility language is traceable to atomic activities."""
    claim_id: str
    experience_id: str
    role_pack: str
    wording: str
    used_facts: Tuple[str, ...]
    activity_id: str
    responsibility_id: str
    evidence_ids: Tuple[str, ...]
    project_responsibility_level: str
    omitted_unknowns: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "bullet-claim-v2", "claim_id": self.claim_id,
            "experience_id": self.experience_id, "role_pack": self.role_pack,
            "wording": self.wording, "used_facts": list(self.used_facts),
            "dependency_refs": {"activity_ids": [self.activity_id], "responsibility_ids": [self.responsibility_id], "completeness": "complete"},
            "evidence_ids": list(self.evidence_ids),
            "project_responsibility_level": self.project_responsibility_level,
            "omitted_unknowns": list(self.omitted_unknowns), "risk_flags": [],
            "verification_status": "candidate", "user_disposition": None,
        }


class BulletComposerService:
    """Converts Canonical Experience and Role Pack into evidence-bound claims.

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
    ) -> List[BulletClaim | BulletClaimV2]:
        """Generate claims from confirmed facts for a specific role pack.

        Args:
            canonical_experience: A validated canonical experience record
            role_pack_name: Name of the role pack (e.g., 'doctoral_v1', 'clinical_research_v1')

        Returns:
            V1 returns up to three claims; V2 returns one claim per confirmed
            atomic task responsibility.

        Raises:
            ValueError: If inputs are invalid or role pack not found
        """
        # v2 consumes confirmed atomic activities.  v1 retains the existing
        # project-level fallback unchanged for legacy sessions.
        if canonical_experience.get("schema_version") == "canonical-experience-v2":
            return self._compose_v2(canonical_experience, role_pack_name)
        if canonical_experience.get("schema_version") != "canonical-experience-v1":
            raise ValueError("canonical_experience must use canonical-experience-v1 or canonical-experience-v2 schema")

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

        # Prefer a medical-specific composition when methods, tools, techniques,
        # or concrete deliverables are available. The generic pattern fallback is
        # kept for sparse input only.
        bullets = self._compose_medical_resume_bullet(
            facts=facts,
            responsibility_level=responsibility_level,
            experience_id=experience_id,
            evidence_ids=evidence_ids,
            role_pack_name=role_pack_name,
        ) or self._generate_bullets(
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

    def _compose_v2(self, canonical_experience: Dict[str, Any], role_pack_name: str) -> List[BulletClaimV2]:
        if canonical_experience.get("status") != "user_confirmed":
            raise ValueError("canonical_experience must have status 'user_confirmed'")
        role_pack = self._load_role_pack(role_pack_name)
        activities = {item.get("activity_id"): item for item in canonical_experience.get("activities", [])}
        responsibilities = canonical_experience.get("task_responsibilities", [])
        if not responsibilities:
            # A v2 record without confirmed task responsibilities must not infer
            # them from tools or methods; use no task-level candidate.
            return []
        claims: List[BulletClaimV2] = []
        ordered = sorted(
            enumerate(responsibilities),
            key=lambda item: self._v2_activity_priority(
                activities.get(item[1].get("activity_id")), role_pack, item[0],
            ),
        )
        for _, responsibility in ordered:
            activity = activities.get(responsibility.get("activity_id"))
            if not activity:
                continue
            components = activity.get("components", {})
            facts: list[str] = []
            rendered: list[str] = []
            for category in ("actions", "methods", "tools", "techniques", "artifacts"):
                values = components.get(category, [])
                facts.extend(f"{category}:{value}" for value in values)
                rendered.extend(FACT_LABELS[category].get(value, value) for value in values)
            if not rendered:
                continue
            wording = self._render_v2_wording(components, responsibility)
            claims.append(BulletClaimV2(
                claim_id=f"claim_{uuid4().hex[:8]}", experience_id=canonical_experience["experience_id"],
                role_pack=role_pack_name, wording=wording, used_facts=tuple(facts),
                activity_id=activity["activity_id"], responsibility_id=responsibility["responsibility_id"],
                evidence_ids=tuple(sorted(set(activity.get("evidence_ids", [])) | set(responsibility.get("evidence_ids", [])))),
                project_responsibility_level=canonical_experience["role"]["responsibility_level"],
                omitted_unknowns=tuple(canonical_experience.get("unknowns", [])),
            ))
        return claims

    @staticmethod
    def _v2_activity_priority(
        activity: Dict[str, Any] | None, role_pack: Dict[str, Any], stable_index: int,
    ) -> tuple[int, int]:
        """Order existing facts by Role Pack emphasis without changing them."""
        components = (activity or {}).get("components", {})
        actions = set(components.get("actions", []))
        capabilities: set[str] = set()
        if actions.intersection({
            "define_research_question", "develop_protocol", "design_search_strategy",
            "screen_studies", "assess_quality", "verify_research_quality",
            "resolve_workflow_issue",
        }) or components.get("methods"):
            capabilities.add("research_method")
        if actions.intersection({"extract_data", "perform_analysis"}) or set(
            components.get("tools", [])
        ).intersection({"r", "python", "spss", "stata", "sas", "revman", "excel"}):
            capabilities.add("data_analysis")
        if actions.intersection({
            "culture_cells", "perform_qpcr", "perform_western_blot",
        }) or components.get("techniques"):
            capabilities.add("wet_lab")
        if actions.intersection({
            "review_clinical_case", "prepare_case_presentation", "develop_protocol",
            "join_ward_rounds", "collect_medical_history", "perform_physical_examination",
            "review_patient_records", "interpret_clinical_findings", "document_clinical_work",
            "communicate_with_patients", "support_clinical_procedure",
            "handover_clinical_information", "follow_clinical_safety",
            "collaborate_clinical_team", "incorporate_clinical_feedback",
        }):
            capabilities.add("clinical_research")
        if actions.intersection({
            "design_search_strategy", "retrieve_literature", "retrieve_guidelines",
            "prepare_research_outputs",
        }):
            capabilities.add("medical_information")
        ranks = {
            capability: index
            for index, capability in enumerate(role_pack.get("priorities", []))
        }
        return min((ranks[item] for item in capabilities if item in ranks), default=len(ranks)), stable_index

    @staticmethod
    def _render_v2_wording(
        components: Dict[str, Any], responsibility: Dict[str, Any],
    ) -> str:
        """Render one atomic activity as natural prose without changing facts."""
        def labels(category: str) -> str:
            return "、".join(
                FACT_LABELS[category].get(value, value)
                for value in components.get(category, [])
            )

        action = next(iter(components.get("actions", [])), "")
        methods, tools = labels("methods"), labels("tools")
        method_phrase = methods.replace("、", "与")
        techniques, artifacts = labels("techniques"), labels("artifacts")
        action_label = FACT_LABELS["actions"].get(action, action or "相关工作")
        if action == "define_research_question":
            body = "研究问题界定"
        elif action == "develop_protocol":
            body = f"{method_phrase}研究方案的制定与修改" if methods else "研究方案的制定与修改"
        elif action == "design_search_strategy":
            body = f"{method_phrase}检索策略设计" if methods else "检索策略设计"
            if tools:
                body += f"，覆盖 {tools}"
        elif action == "retrieve_literature":
            body = "医学文献检索"
            if tools:
                body += f"，使用 {tools}"
        elif action == "screen_studies":
            body = "文献筛选"
        elif action == "extract_data":
            body = "研究数据提取"
        elif action == "assess_quality":
            body = f"{method_phrase}的质量评价与偏倚评估" if methods else "质量评价与偏倚评估"
        elif action == "verify_research_quality":
            body = "研究过程的质量复核与一致性检查"
        elif action == "resolve_workflow_issue":
            body = "研究流程中的问题核查与处理"
        elif action == "review_clinical_case":
            body = "病例信息梳理与临床思路讨论"
            if tools:
                body += f"，参考 {tools}"
            if artifacts:
                body += f"，形成{artifacts}"
        elif action == "retrieve_guidelines":
            body = "围绕具体病例查阅临床指南与医学证据"
        elif action == "interpret_clinical_findings":
            body = "检查与检验结果梳理，并参与临床判断讨论"
        elif action == "document_clinical_work":
            body = "临床信息整理与记录书写"
            if artifacts:
                body += f"，形成{artifacts}"
        elif action == "follow_clinical_safety":
            body = "医疗安全、感染防控与患者隐私规范执行"
        elif action == "collaborate_clinical_team":
            body = "临床信息沟通与团队协作"
        elif action == "incorporate_clinical_feedback":
            body = "根据带教反馈改进临床信息采集、记录或汇报方式"
        elif action == "prepare_research_outputs":
            body = "研究材料整理"
            if artifacts:
                body += f"，形成{artifacts}"
        elif action == "perform_analysis":
            body = "统计分析"
            if methods:
                body += f"，采用 {methods}"
            if tools:
                body += f"并使用 {tools}"
            if techniques:
                body += f"，涉及 {techniques}"
            if artifacts:
                body += f"，形成{artifacts}"
        else:
            body = action_label
            if methods:
                body += f"，采用 {methods}"
            if tools:
                body += f"，使用 {tools}"
            if techniques:
                body += f"，涉及 {techniques}"
            if artifacts:
                body += f"，形成{artifacts}"

        ownership = responsibility.get("ownership_level")
        execution = responsibility.get("execution_mode")
        partial = (responsibility.get("scope") or {}).get("coverage") == "partial"
        if partial:
            lead = {
                "supervised": "在指导下完成已分配的",
                "shared": "与团队共同完成已分配的",
                "independent": "独立完成已分配的",
            }.get(execution, "完成已分配的")
        elif execution == "supervised":
            lead = "在指导下参与"
        elif execution == "shared":
            lead = "与团队共同完成"
        elif ownership == "owned_component" and execution == "independent":
            lead = "独立完成"
        elif ownership == "led_delivery":
            lead = "推动完成"
        else:
            lead = "参与完成"
        return f"{lead}{body}。"

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
            "actions", "methods", "tools", "techniques", "objects", "collaboration",
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

    def _compose_medical_resume_bullet(
        self,
        *,
        facts: Dict[str, Any],
        responsibility_level: str,
        experience_id: str,
        evidence_ids: Tuple[str, ...],
        role_pack_name: str,
    ) -> List[BulletClaim]:
        """Build one dense, evidence-bound bullet for common medical experiences.

        Role packs change the ordering and emphasis, but never upgrade the
        user's responsibility or introduce a result absent from the facts.
        """
        methods = facts.get("methods", [])
        techniques = facts.get("techniques", [])
        actions = facts.get("actions", [])
        tools = facts.get("tools", [])
        artifacts = facts.get("artifacts", [])

        action_labels = {
            **FACT_LABELS["actions"],
            "retrieve_literature": "文献检索", "perform_analysis": "数据分析",
            "perform_qpcr": "qPCR 检测",
            "perform_western_blot": "Western Blot 检测",
            "prepare_case_presentation": "病例汇报材料制作",
            "retrieve_guidelines": "指南与文献检索",
        }
        method_labels = {
            **FACT_LABELS["methods"],
            "mendelian_randomization": "孟德尔随机化（MR）",
        }
        technique_labels = FACT_LABELS["techniques"]
        tool_labels = FACT_LABELS["tools"]

        known_facts = (
            set(actions).intersection(action_labels)
            or set(methods).intersection(method_labels)
            or set(techniques).intersection(technique_labels)
            or set(tools).intersection(tool_labels)
        )
        if not known_facts:
            return []

        def labels(items: List[str], mapping: Dict[str, str]) -> str:
            return "、".join(mapping.get(item, item) for item in items)

        action_text = labels(actions, action_labels)
        method_text = labels(methods, method_labels).replace("、", "及")
        technique_text = labels(techniques, technique_labels)
        tool_text = labels(tools, tool_labels)
        literature_tools = labels(
            [tool for tool in tools if tool in {"pubmed", "embase", "cochrane"}],
            tool_labels,
        )
        analysis_tools = labels(
            [tool for tool in tools if tool not in {"pubmed", "embase", "cochrane"}],
            tool_labels,
        )
        has_meta = "meta_analysis" in methods
        has_case = "review_clinical_case" in actions
        topic = (facts.get("context") or {}).get("topic")
        topic_scope = f"围绕{topic}的" if topic else ""
        responsibility_verb = {
            "participated": "参与",
            "owned_component": "负责",
            "led_delivery": "主导",
            "project_owner": "负责",
        }.get(responsibility_level, "参与")

        if has_case:
            wording = f"{responsibility_verb}{topic_scope}临床病例鉴别诊断、检查结果与诊疗思路梳理"
            if "retrieve_guidelines" in actions:
                wording += "，检索相关指南与文献"
            if "case_presentation_material" in artifacts:
                wording += "，制作病例汇报材料并完成现场汇报"
        elif has_meta:
            workflow = labels(
                [item for item in actions if item in {"retrieve_literature", "screen_studies", "extract_data"}],
                action_labels,
            )
            if role_pack_name == "health_ai_data_v1" and analysis_tools:
                wording = f"{responsibility_verb}{topic_scope}{method_text}的数据整理与分析，使用 {analysis_tools} 完成统计计算"
                if workflow:
                    wording += f"，覆盖{workflow}"
            elif role_pack_name == "medical_affairs_v1":
                wording = f"{responsibility_verb}{topic_scope}医学证据整理"
                if literature_tools:
                    wording += f"，使用 {literature_tools} 进行检索"
                if workflow:
                    wording += f"，完成{workflow}"
                if analysis_tools:
                    wording += f"，使用 {analysis_tools} 完成 {method_text}"
            elif role_pack_name == "clinical_research_v1":
                wording = f"{responsibility_verb}{topic_scope}{method_text}的证据分析"
                if workflow:
                    wording += f"，完成{workflow}"
                if analysis_tools:
                    wording += f"，使用 {analysis_tools} 完成统计分析"
            else:
                wording = f"{responsibility_verb}{topic_scope}{method_text}"
                if workflow:
                    wording += f"，完成{workflow}"
                if literature_tools:
                    wording += f"，使用 {literature_tools} 进行证据检索"
                if analysis_tools:
                    wording += f"，使用 {analysis_tools} 完成分析"
            if "analysis_figures" in artifacts:
                wording += "并整理结果图表"
            if "group_presentation" in artifacts:
                wording += "，参与组会汇报"
        elif technique_text:
            wording = f"{responsibility_verb}{topic_scope}实验执行，完成{technique_text}"
            if "analysis_figures" in artifacts:
                wording += "，记录原始数据并整理结果图表"
            if "group_presentation" in artifacts:
                wording += "，参与组会讨论"
        else:
            wording = f"{responsibility_verb}医学研究工作"
            if action_text:
                wording += f"，完成{action_text}"
            if method_text:
                wording += f"，采用{method_text}"
            if tool_text:
                wording += f"，使用{tool_text}"

        wording = wording.rstrip("，。") + "。"

        claim_id = f"claim_{uuid4().hex[:8]}"
        used_facts = []
        if topic:
            used_facts.append("context:topic")
        for category in ("actions", "methods", "tools", "techniques", "artifacts"):
            used_facts.extend(f"{category}:{item}" for item in facts.get(category, []))

        return [BulletClaim(
            claim_id=claim_id,
            experience_id=experience_id,
            role_pack=role_pack_name,
            wording=wording,
            used_facts=tuple(used_facts),
            evidence_ids=evidence_ids,
            responsibility_level=responsibility_level,
            omitted_unknowns=tuple(facts.get("unknowns", [])),
            risk_flags=(),
        )]

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
