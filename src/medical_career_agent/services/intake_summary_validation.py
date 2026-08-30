from __future__ import annotations

from typing import Any

from .resume_vocabulary import flat_fact_labels


class IntakeSummaryValidationService:
    """Validate model-authored intake copy without granting fact authority."""

    _LABELS = {
        **flat_fact_labels(),
        "participated": "参与", "contributed": "参与 / 协助",
        "owned_component": "负责明确模块", "supervised": "在指导下完成",
        "shared": "共同完成", "independent": "独立完成",
    }

    @classmethod
    def validate(
        cls,
        *,
        candidate: dict[str, Any] | None,
        extracted_facts: dict[str, Any],
        evidence_texts: list[str],
        question_card: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(candidate, dict):
            return cls._rejected("模型没有返回结构化整理结果。")
        summary = candidate.get("summary")
        if not isinstance(summary, dict):
            return cls._rejected("模型整理缺少摘要对象。")
        fact_refs = summary.get("fact_refs")
        quotes = summary.get("evidence_quotes")
        if not isinstance(fact_refs, list) or not fact_refs or not all(isinstance(item, str) for item in fact_refs):
            return cls._rejected("模型摘要缺少可校验的事实引用。")
        if not isinstance(quotes, list) or not quotes or not all(
            isinstance(item, str) and item.strip()
            and any(item in evidence_text for evidence_text in evidence_texts)
            for item in quotes
        ):
            return cls._rejected("模型摘要的原文引用无法定位。")
        allowed_refs = cls.fact_refs(extracted_facts)
        if not set(fact_refs).issubset(allowed_refs):
            return cls._rejected("模型摘要引用了后端事实白名单之外的内容。")
        question = cls._validated_question(candidate.get("next_question"), question_card)
        return {
            "status": "validated", "summary_source": "llm_validated",
            "summary": cls._render_summary(fact_refs), "fact_refs": fact_refs,
            "evidence_quotes": quotes, "next_question": question,
            "error": None,
        }

    @staticmethod
    def fact_refs(facts: dict[str, Any]) -> set[str]:
        refs: set[str] = set()
        for category, value in facts.items():
            if isinstance(value, list):
                refs.update(f"{category}:{item}" for item in value if isinstance(item, (str, int, float)))
            elif isinstance(value, dict):
                refs.update(
                    f"{category}.{key}:{item}" for key, item in value.items()
                    if isinstance(item, (str, int, float, bool)) and item not in ("", None)
                )
        return refs

    @staticmethod
    def _validated_question(candidate: Any, card: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(candidate, dict) or not isinstance(card, dict):
            return None
        if candidate.get("question_id") != card.get("question_id"):
            return None
        recommended = candidate.get("recommended_option_ids", [])
        allowed_options = {item.get("id") for item in card.get("options", [])}
        if not isinstance(recommended, list) or not all(isinstance(item, str) for item in recommended):
            return None
        if not set(recommended).issubset(allowed_options):
            return None
        return {
            "question_id": card["question_id"],
            "recommended_option_ids": recommended,
        }

    @classmethod
    def _render_summary(cls, fact_refs: list[str]) -> str:
        grouped: dict[str, list[str]] = {}
        for ref in fact_refs:
            category, _, value = ref.partition(":")
            if not value:
                continue
            grouped.setdefault(category.split(".", 1)[0], []).append(cls._LABELS.get(value, value))
        clauses = []
        for category, prefix in (
            ("context", "项目背景涉及"), ("actions", "你提到的实际工作包括"),
            ("methods", "使用的方法包括"), ("tools", "使用的工具或资源包括"),
            ("techniques", "涉及的技术包括"), ("artifacts", "形成的材料包括"),
            ("objects", "处理对象包括"), ("outcomes", "项目状态包括"),
            ("scope", "范围信息包括"), ("collaboration", "协作对象包括"),
            ("role", "责任边界为"),
        ):
            values = list(dict.fromkeys(grouped.get(category, [])))
            if values:
                clauses.append(f"{prefix}{'、'.join(values)}")
        return "我目前根据你的原话整理到：" + "；".join(clauses) + "。"

    @staticmethod
    def _rejected(error: str) -> dict[str, Any]:
        return {
            "status": "rejected", "summary_source": "pending",
            "summary": None, "fact_refs": [], "evidence_quotes": [],
            "next_question": None, "error": error,
        }
