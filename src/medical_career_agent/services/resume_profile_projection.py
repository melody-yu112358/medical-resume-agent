from __future__ import annotations

from collections.abc import Iterable
from typing import Any


METHOD_LABELS = {
    "systematic_review": "系统综述",
    "meta_analysis": "Meta 分析",
    "mendelian_randomization": "孟德尔随机化（MR）",
    "sensitivity_analysis": "敏感性分析",
    "randomized_trial": "随机对照试验",
    "cohort_study": "队列研究",
    "case_control": "病例对照研究",
}

TOOL_LABELS = {
    "spss": ("SPSS", "data"),
    "r": ("R", "data"),
    "python": ("Python", "data"),
    "sql": ("SQL", "data"),
    "stata": ("Stata", "data"),
    "sas": ("SAS", "data"),
    "excel": ("Excel", "data"),
    "revman": ("RevMan", "data"),
    "graphpad_prism": ("GraphPad Prism", "data"),
    "endnote": ("EndNote", "data"),
    "noteexpress": ("NoteExpress", "data"),
    "pubmed": ("PubMed", "medical_information"),
    "embase": ("Embase", "medical_information"),
    "cochrane": ("Cochrane Library", "medical_information"),
}


def project_confirmed_profile(canonicals: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Project positioning and skills from evidence-bound confirmed facts only."""
    projected: dict[tuple[str, str], set[str]] = {}

    def add(category: str, name: str, evidence_ids: Iterable[str]) -> None:
        evidence = {item for item in evidence_ids if item}
        if evidence:
            projected.setdefault((category, name), set()).update(evidence)

    for canonical in canonicals:
        if canonical.get("status") != "user_confirmed":
            continue
        canonical_evidence = set(canonical.get("evidence_ids") or [])
        if canonical.get("schema_version") == "canonical-experience-v2":
            sources = (
                (activity.get("components") or {}, canonical_evidence.intersection(activity.get("evidence_ids") or []))
                for activity in canonical.get("activities") or []
                if activity.get("status") == "user_confirmed"
            )
        else:
            sources = ((canonical, canonical_evidence),)

        for components, evidence_ids in sources:
            for method_id in components.get("methods") or []:
                if method_id in METHOD_LABELS:
                    add("research", METHOD_LABELS[method_id], evidence_ids)
            for tool_id in components.get("tools") or []:
                if tool_id in TOOL_LABELS:
                    name, category = TOOL_LABELS[tool_id]
                    add(category, name, evidence_ids)

    skills = [
        {"name": name, "category": category, "level": None, "evidence_ids": sorted(evidence_ids)}
        for (category, name), evidence_ids in projected.items()
    ]
    methods = [item for item in skills if item["category"] == "research"]
    positioning_skills = (methods + [item for item in skills if item["category"] != "research"])[:3]
    if not methods or len(skills) < 2:
        positioning_skills = []
    names = [item["name"] for item in positioning_skills]
    joined_names = f"{'、'.join(names[:-1])}与{names[-1]}" if len(names) > 1 else ""
    summary = f"基于已确认经历，积累了{joined_names}相关实践。" if joined_names else None
    summary_evidence_ids = sorted({
        evidence_id for item in positioning_skills
        for evidence_id in item["evidence_ids"]
    })
    return {"summary": summary, "summary_evidence_ids": summary_evidence_ids, "skills": skills}
