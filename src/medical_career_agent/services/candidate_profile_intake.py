from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


class CandidateProfileInputError(ValueError):
    """Raised when a bounded profile answer cannot be accepted."""


class CandidateProfileIntakeService:
    """Collect candidate basics and one education record without creating claims."""

    QUESTIONS = (
        {
            "id": "name", "section": "basics", "label": "你的姓名是？",
            "help": "将用于简历抬头；只填写你希望在简历中展示的姓名。",
            "kind": "text", "required": True, "placeholder": "例如：张同学",
        },
        {
            "id": "email", "section": "basics", "label": "你的联系邮箱是？",
            "help": "如果暂时不想填写，可以跳过，之后仍可补充。",
            "kind": "email", "required": False, "placeholder": "例如：name@example.com",
        },
        {
            "id": "phone", "section": "basics", "label": "你的联系电话是？",
            "help": "如果暂时不想填写，可以跳过。",
            "kind": "text", "required": False, "placeholder": "例如：138 0000 0000",
        },
        {
            "id": "location", "section": "basics", "label": "你目前所在的城市是？",
            "help": "填写城市即可；如果求职地点尚未确定，可以跳过。",
            "kind": "text", "required": False, "placeholder": "例如：上海",
        },
        {
            "id": "institution", "section": "education", "label": "你目前或最近就读的学校是？",
            "help": "先采集一段主要教育经历，后续可继续增加。",
            "kind": "text", "required": True, "placeholder": "例如：示例医科大学",
        },
        {
            "id": "degree", "section": "education", "label": "这段教育经历对应什么学历或学位？",
            "help": "选择最接近的一项，也可以填写其他真实情况。",
            "kind": "single_choice", "required": False,
            "options": ["本科", "医学学士", "硕士", "医学硕士", "博士", "医学博士", "专科", "其他"],
            "placeholder": "其他学历或学位（可选）",
        },
        {
            "id": "major", "section": "education", "label": "你的专业是什么？",
            "help": "填写学校正式使用的专业名称。",
            "kind": "text", "required": False, "placeholder": "例如：临床医学",
        },
        {
            "id": "period", "section": "education", "label": "这段教育经历的就读时间是？",
            "help": "填写开始年月；如果仍在读，结束时间选择“至今”。",
            "kind": "period", "required": False,
        },
    )

    @classmethod
    def initial_state(cls) -> dict[str, Any]:
        return {
            "schema_version": "candidate-profile-v1",
            "status": "collecting",
            "current_question_id": cls.QUESTIONS[0]["id"],
            "answers": {},
            "profile_evidence_records": [],
        }

    @classmethod
    def current_question(cls, profile: dict[str, Any]) -> dict[str, Any] | None:
        if profile.get("status") != "collecting":
            return None
        question_id = profile.get("current_question_id")
        question = next((item for item in cls.QUESTIONS if item["id"] == question_id), None)
        if question is None:
            return None
        result = deepcopy(question)
        result["position"] = next(index for index, item in enumerate(cls.QUESTIONS, 1) if item["id"] == question_id)
        result["total"] = len(cls.QUESTIONS)
        return result

    @classmethod
    def answer(
        cls, profile: dict[str, Any], *, question_id: str, value: Any, skipped: bool = False,
    ) -> dict[str, Any]:
        question = cls.current_question(profile)
        if question is None or question_id != question["id"]:
            raise CandidateProfileInputError("请回答当前显示的问题。")
        if skipped and question["required"]:
            raise CandidateProfileInputError("这一项是生成可用简历所必需的，请填写后继续。")
        normalized = None if skipped else cls._normalize(question, value)
        if question["required"] and normalized in (None, ""):
            raise CandidateProfileInputError("这一项不能为空。")
        profile.setdefault("answers", {})[question_id] = normalized
        next_index = question["position"]
        if next_index >= len(cls.QUESTIONS):
            profile["current_question_id"] = None
            profile["status"] = "awaiting_confirmation"
        else:
            profile["current_question_id"] = cls.QUESTIONS[next_index]["id"]
        return profile

    @classmethod
    def confirm(cls, profile: dict[str, Any]) -> dict[str, Any]:
        if profile.get("status") != "awaiting_confirmation":
            raise CandidateProfileInputError("请先完成当前资料采集。")
        answers = profile.get("answers") or {}
        if not answers.get("name") or not answers.get("institution"):
            raise CandidateProfileInputError("姓名和学校尚未填写完整。")
        records = []
        for index, question in enumerate(cls.QUESTIONS, 1):
            value = answers.get(question["id"])
            if value in (None, "", {}):
                continue
            statement = cls._statement(question, value)
            records.append({
                "evidence_id": f"profile_ev_{index:03d}",
                "field": question["id"],
                "section": question["section"],
                "source_text": statement,
                "status": "confirmed",
            })
        profile["profile_evidence_records"] = records
        profile["status"] = "confirmed"
        return profile

    @classmethod
    def restart(cls, profile: dict[str, Any]) -> dict[str, Any]:
        profile["status"] = "collecting"
        profile["current_question_id"] = cls.QUESTIONS[0]["id"]
        profile["profile_evidence_records"] = []
        return profile

    @classmethod
    def document_sections(cls, profile: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        if profile.get("status") != "confirmed":
            return (
                {"name": None, "phone": None, "email": None, "location": None, "summary": None, "evidence_ids": []},
                [],
                [],
            )
        answers = profile.get("answers") or {}
        records = profile.get("profile_evidence_records") or []
        ids_by_section = {
            section: [item["evidence_id"] for item in records if item.get("section") == section]
            for section in ("basics", "education")
        }
        period = answers.get("period") or {}
        basics = {
            "name": answers.get("name"), "phone": answers.get("phone"),
            "email": answers.get("email"), "location": answers.get("location"),
            "summary": None, "evidence_ids": ids_by_section["basics"],
        }
        education = [{
            "item_id": "education_001", "institution": answers.get("institution"),
            "degree": answers.get("degree"), "major": answers.get("major"),
            "period": {
                "start": period.get("start"), "end": period.get("end"),
                "ongoing": bool(period.get("ongoing", False)),
            },
            "ranking_or_gpa": None, "highlights": [],
            "evidence_ids": ids_by_section["education"],
        }]
        evidence = [{
            "evidence_id": item["evidence_id"], "statement": item["source_text"],
            "source_document_id": None, "source_locator": None,
            "status": "user_confirmed", "confirmed_at": None,
        } for item in records]
        return basics, education, evidence

    @staticmethod
    def _normalize(question: dict[str, Any], value: Any) -> Any:
        if question["kind"] == "period":
            if not isinstance(value, dict):
                raise CandidateProfileInputError("就读时间格式不正确。")
            start = str(value.get("start", "")).strip() or None
            ongoing = bool(value.get("ongoing", False))
            end = None if ongoing else (str(value.get("end", "")).strip() or None)
            if not start and not end and not ongoing:
                return None
            return {"start": start, "end": end, "ongoing": ongoing}
        normalized = str(value or "").strip()
        if question["kind"] == "email" and normalized and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise CandidateProfileInputError("邮箱格式看起来不完整，请检查后重试。")
        return normalized or None

    @staticmethod
    def _statement(question: dict[str, Any], value: Any) -> str:
        if question["kind"] == "period":
            end = "至今" if value.get("ongoing") else (value.get("end") or "结束时间未填写")
            return f"就读时间：{value.get('start') or '开始时间未填写'} 至 {end}"
        return f"{question['label'].rstrip('？')}：{value}"
