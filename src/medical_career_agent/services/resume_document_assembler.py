from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .bullet_composer import BulletClaim


@dataclass(frozen=True)
class ResumeDocument:
    """完整的简历文档结构。"""

    schema_version: str
    resume_id: str
    target: str
    basics: Dict[str, Any]
    education: List[Dict[str, Any]]
    research_experience: List[Dict[str, Any]]
    clinical_experience: List[Dict[str, Any]]
    professional_experience: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    publications: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    languages: List[Dict[str, Any]]
    capability_profile: List[Dict[str, Any]]
    research_interests: List[str]
    evidence: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "resume_id": self.resume_id,
            "target": self.target,
            "basics": self.basics,
            "education": self.education,
            "research_experience": self.research_experience,
            "clinical_experience": self.clinical_experience,
            "professional_experience": self.professional_experience,
            "projects": self.projects,
            "publications": self.publications,
            "skills": self.skills,
            "languages": self.languages,
            "capability_profile": self.capability_profile,
            "research_interests": self.research_interests,
            "evidence": self.evidence
        }


class ResumeDocumentAssembler:
    """组装完整的简历文档。"""

    def __init__(self):
        pass

    def assemble_resume_document(
        self,
        *,
        candidate_facts: Dict[str, Any],
        three_tier_results: List[Any],  # ThreeTierExpressionResult objects
        target_roles: List[str],
        expression_tier: str = "professional"
    ) -> ResumeDocument:
        """组装完整的简历文档。"""
        # 创建基本信息
        basics = self._create_basics(candidate_facts)

        # 创建教育背景
        education = self._create_education(candidate_facts)

        # 创建经历部分 - properly route each experience based on its domain
        research_experience = []
        clinical_experience = []
        professional_experience = []
        projects = []

        canonical_experiences = candidate_facts.get("canonical_experiences", [])

        for i, (result, canonical_exp) in enumerate(zip(three_tier_results, canonical_experiences)):
            if expression_tier == "conservative":
                claims = result.conservative_claims
            elif expression_tier == "high_impact":
                claims = result.high_impact_claims
            else:
                claims = result.professional_claims

            experience_section = self._create_experience_section(result.experience_id, claims, canonical_exp)

            # 根据经历类型分配到不同部分 using the actual canonical experience context
            context = canonical_exp.get("context", {})
            domain = context.get("domain", "clinical_research")

            if domain == "clinical_research":
                research_experience.append(experience_section)
            elif domain == "clinical_practice":
                clinical_experience.append(experience_section)
            elif domain == "wet_lab" or domain == "data_analysis":
                professional_experience.append(experience_section)
            elif domain == "epidemiology_research":
                projects.append(experience_section)
            else:
                # Default to projects for unknown domains
                projects.append(experience_section)

        # 创建其他部分
        publications = self._create_publications(candidate_facts)
        skills = self._create_skills(candidate_facts)
        languages = self._create_languages(candidate_facts)
        capability_profile = self._create_capability_profile(candidate_facts)
        research_interests = list(candidate_facts.get("research_interests", []))
        evidence = self._create_evidence(candidate_facts)

        return ResumeDocument(
            schema_version="resume-document-v1",
            resume_id=f"resume_{candidate_facts.get('session_id', 'unknown')}",
            target=target_roles[0] if target_roles else "doctoral_v1",
            basics=basics,
            education=education,
            research_experience=research_experience,
            clinical_experience=clinical_experience,
            professional_experience=professional_experience,
            projects=projects,
            publications=publications,
            skills=skills,
            languages=languages,
            capability_profile=capability_profile,
            research_interests=research_interests,
            evidence=evidence
        )

    def _create_basics(self, candidate_facts: Dict[str, Any]) -> Dict[str, Any]:
        """创建基本信息。"""
        supplied = candidate_facts.get("basics", {})
        objective = candidate_facts.get("career_objective", {})
        return {
            "name": supplied.get("name", ""),
            "phone": supplied.get("phone", ""),
            "email": supplied.get("email", ""),
            "location": supplied.get("location", ""),
            "target": supplied.get("target", objective.get("target_direction", "")),
            "avatar_path": supplied.get("avatar_path", ""),
            "summary": candidate_facts.get("overview", ""),
            "evidence_ids": ["ev_overview"]
        }

    def _create_education(self, candidate_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建教育背景。"""
        education = candidate_facts.get("education")
        if not education:
            return []
        gpa = education.get("gpa", "")
        ranking = education.get("ranking", "")
        ranking_or_gpa = " | ".join(part for part in (gpa, ranking) if part)
        return [{
            "item_id": "edu_001",
            "institution": education.get("institution", ""),
            "degree": education.get("degree", ""),
            "major": education.get("major", ""),
            "period": education.get("period", {}),
            "ranking_or_gpa": ranking_or_gpa,
            "highlights": (["核心课程：" + "、".join(education.get("core_courses", []))]
                           if education.get("core_courses") else []),
            "evidence_ids": ["ev_education"]
        }]

    def _create_experience_section(self, experience_id: str, claims: List[BulletClaim], canonical_experience: Dict[str, Any]) -> Dict[str, Any]:
        """创建经历部分。"""
        bullets = []
        for claim in claims:
            bullet = {
                "text": claim.wording,
                "dimension_id": claim.dimension_id,
                "claim_type": claim.claim_type,
                "expression_tier": claim.expression_tier,
                "evidence_ids": list(claim.evidence_ids),
            }
            if claim.source_fact_ids:
                bullet["source_fact_ids"] = list(claim.source_fact_ids)
            if claim.role_value:
                bullet["role_value"] = claim.role_value
            bullets.append(bullet)

        # Extract experience details from canonical experience
        context = canonical_experience.get("context", {})
        domain = context.get("domain", "clinical_research")

        organization = canonical_experience.get("organization", "")
        title = canonical_experience.get("title", canonical_experience.get("role", {}).get("title", ""))
        department_or_field = canonical_experience.get(
            "department_or_field", canonical_experience.get("context", {}).get("topic", "")
        )
        period = canonical_experience.get("period", {})

        return {
            "item_id": experience_id,
            "organization": organization,
            "title": title,
            "department_or_field": department_or_field,
            "period": period,
            "bullets": bullets,
            "evidence_ids": canonical_experience.get("evidence_ids", ["ev_experience"])
        }

    def _create_publications(self, candidate_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建出版物部分。"""
        output = candidate_facts.get("meta_analysis_experience", {}).get("academic_output")
        if not output:
            return []
        return [{
            "item_id": "pub_001",
            "title": output.get("paper_title", ""),
            "venue": output.get("venue", ""),
            "status": output.get("status", ""),
            "author_position": output.get("author_position", ""),
            "year": output.get("year"),
            "evidence_ids": ["ev_publication"]
        }]

    def _create_skills(self, candidate_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建技能部分。"""
        source = candidate_facts.get("skills_and_certificates", {})
        skills: List[Dict[str, Any]] = []
        for name, level in source.get("data_analysis", {}).items():
            skills.append({"name": name, "category": "data", "level": level,
                           "evidence_ids": ["ev_skills"]})
        for name, level in source.get("literature_management", {}).items():
            skills.append({"name": name, "category": "medical_information", "level": level,
                           "evidence_ids": ["ev_skills"]})
        return skills

    def _create_languages(self, candidate_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建语言部分。"""
        values = candidate_facts.get("skills_and_certificates", {}).get("languages", {})
        labels = {"English": "英语", "Chinese": "中文"}
        return [{"language": labels.get(name, name), "level_or_score": level,
                 "evidence_ids": ["ev_language"]} for name, level in values.items()]

    def _create_capability_profile(self, candidate_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建能力档案。"""
        return list(candidate_facts.get("capability_profile", []))

    def _create_evidence(self, candidate_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建证据部分。"""
        return list(candidate_facts.get("evidence", [])) or [{
            "evidence_id": "ev_overview",
            "statement": candidate_facts.get("overview", ""),
            "status": "user_confirmed",
            "confirmed_at": candidate_facts.get("confirmed_at")
        }]


# Role Pack深化
def enhance_role_packs():
    """深化四个医学Role Pack。"""
    role_packs_dir = Path(__file__).parent.parent.parent.parent / "data" / "role-packs"

    # Doctoral V1 - 考博/保研
    doctoral_v1 = {
        "role_pack": "doctoral_v1",
        "label": "Doctoral / Graduate School",
        "priorities": ["research_methodology", "statistical_rigor", "academic_contribution", "methodology_depth"],
        "value_mappings": {
            "clinical_research": ["demonstrates research methodology competence", "shows mastery of systematic review methodology fundamentals"]
        },
        "preferred_actions": ["design", "implement", "analyze", "interpret", "synthesize"],
        "allowed_verbs": ["参与", "协助", "contributed to", "supported", "participated in", "assisted with"],
        "restricted_verbs": ["独立", "主导", "负责整体"],
        "forbidden_claims": ["developed novel methodology", "resolved all heterogeneity issues", "concluded definitive treatment recommendations"],
        "sentence_patterns": [
            "{responsibility} {action} {object} using {method}, ensuring methodological rigor",
            "Applied {method} to {action} {object}, demonstrating research competence",
            "{action} {object} through {method}, contributing to evidence base"
        ],
        "evaluation_cases": []
    }

    # Clinical Research V1 - 临床研究
    clinical_research_v1 = {
        "role_pack": "clinical_research_v1",
        "label": "Clinical Research",
        "priorities": ["protocol_execution", "data_quality", "regulatory_compliance", "team_collaboration"],
        "value_mappings": {
            "clinical_research": ["executes systematic review protocols with precision", "ensures high-quality data extraction and management"]
        },
        "preferred_actions": ["execute", "collect", "validate", "manage", "coordinate"],
        "allowed_verbs": ["参与", "协助", "执行", "完成", "support", "assist", "execute", "complete"],
        "restricted_verbs": ["独立设计", "主导开发", "负责整体"],
        "forbidden_claims": ["designed clinical trial", "obtained IRB approval independently", "managed entire clinical study"],
        "sentence_patterns": [
            "{responsibility} {action} {object} following established protocols, ensuring data quality",
            "Executed {method} {action} {object}, maintaining regulatory compliance",
            "{action} {object} as part of research team, supporting study objectives"
        ],
        "evaluation_cases": []
    }

    # Medical Affairs V1 - 医学事务/MSL
    medical_affairs_v1 = {
        "role_pack": "medical_affairs_v1",
        "label": "Medical Affairs / MSL",
        "priorities": ["evidence_synthesis", "scientific_communication", "therapeutic_expertise", "stakeholder_engagement"],
        "value_mappings": {
            "clinical_research": ["synthesizes complex medical evidence comprehensively", "communicates evidence findings clearly and accurately"]
        },
        "preferred_actions": ["synthesize", "communicate", "translate", "present", "engage"],
        "allowed_verbs": ["参与", "协助", "支持", "促进", "participated", "supported", "facilitated", "promoted"],
        "restricted_verbs": ["独立负责", "主导沟通", "管理关系"],
        "forbidden_claims": ["authored entire manuscript independently", "created regulatory document that gained approval"],
        "sentence_patterns": [
            "{responsibility} {action} {object} to synthesize medical evidence, supporting scientific communication",
            "Communicated {method} findings on {object}, demonstrating therapeutic expertise",
            "{action} {object} translating complex evidence for stakeholder understanding"
        ],
        "evaluation_cases": []
    }

    # Health AI Data V1 - 医疗AI/数据
    health_ai_data_v1 = {
        "role_pack": "health_ai_data_v1",
        "label": "Health AI / Data",
        "priorities": ["data_curation", "systematic_approach", "quality_assurance", "analytical_rigor"],
        "value_mappings": {
            "clinical_research": ["curates high-quality structured data from literature", "applies systematic methodology to data collection"]
        },
        "preferred_actions": ["curate", "analyze", "engineer", "build", "develop"],
        "allowed_verbs": ["参与", "协助", "支持", "contributed to", "supported", "assisted with"],
        "restricted_verbs": ["独立开发", "主导构建", "负责系统"],
        "forbidden_claims": ["built production-ready AI system", "developed novel algorithm"],
        "sentence_patterns": [
            "{responsibility} {action} {object} creating high-quality structured data, ensuring analytical rigor",
            "Applied systematic {method} to {action} {object}, building robust data processes",
            "{action} {object} engineering scalable analytical workflows for medical data"
        ],
        "evaluation_cases": []
    }

    # 保存Role Packs
    role_packs_dir.mkdir(exist_ok=True)
    (role_packs_dir / "doctoral_v1.json").write_text(json.dumps(doctoral_v1, ensure_ascii=False, indent=2), encoding="utf-8")
    (role_packs_dir / "clinical_research_v1.json").write_text(json.dumps(clinical_research_v1, ensure_ascii=False, indent=2), encoding="utf-8")
    (role_packs_dir / "medical_affairs_v1.json").write_text(json.dumps(medical_affairs_v1, ensure_ascii=False, indent=2), encoding="utf-8")
    (role_packs_dir / "health_ai_data_v1.json").write_text(json.dumps(health_ai_data_v1, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    # 增强Role Packs
    enhance_role_packs()
    print("✅ Role Packs enhanced successfully!")

    # 测试Resume Document Assembler
    assembler = ResumeDocumentAssembler()
    print("✅ Resume Document Assembler implemented!")
