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
        {
            "id": "ranking_or_gpa", "section": "education", "evidence_index": 13,
            "label": "是否希望展示 GPA、成绩排名或综合排名？",
            "help": "只填写可以确认的原始表述；没有或不适合展示可以跳过。",
            "kind": "text", "required": False, "placeholder": "例如：GPA 3.6/4.0；专业前 15%",
        },
        {
            "id": "education_highlights", "section": "education", "evidence_index": 14,
            "label": "有哪些与申请方向相关的核心课程或教育亮点？",
            "help": "一行填写一项，只保留确实修读或完成的内容。",
            "kind": "multiline_list", "required": False,
            "placeholder": "例如：医学统计学\n循证医学\n流行病学",
        },
        {
            "id": "awards", "section": "awards", "evidence_index": 9, "label": "有哪些希望展示的荣誉或奖项？",
            "help": "一行填写一项，只写真实名称；颁发单位或年份不确定时不要补写。",
            "kind": "multiline_list", "required": False,
            "placeholder": "例如：2024 年国家奖学金\n校级科研竞赛一等奖",
        },
        {
            "id": "languages", "section": "languages", "evidence_index": 10, "label": "有哪些语言成绩或能力需要展示？",
            "help": "一行填写一项，分数或等级只在能够确认时填写。",
            "kind": "multiline_list", "required": False,
            "placeholder": "例如：CET-4：620\nCET-6：580",
        },
        {
            "id": "certificates", "section": "certificates", "evidence_index": 11, "label": "有哪些证书或正式培训需要展示？",
            "help": "一行填写一项；课程接触不等于持有证书，没有可以跳过。",
            "kind": "multiline_list", "required": False,
            "placeholder": "例如：GCP 培训证书",
        },
        {
            "id": "academic_outputs", "section": "publications", "evidence_index": 15,
            "label": "是否有论文、投稿、会议摘要、海报或学术汇报？",
            "help": "一行填写一项，并保留真实状态和作者信息；未投稿不能写成已投稿。",
            "kind": "multiline_list", "required": False,
            "placeholder": "例如：心血管系统综述论文初稿，共同作者，尚未投稿",
        },
        {
            "id": "research_interests", "section": "research_interests", "evidence_index": 12, "label": "有哪些真实的研究兴趣希望展示？",
            "help": "一行填写一个方向；这只是兴趣陈述，不会被写成已有成果。",
            "kind": "multiline_list", "required": False,
            "placeholder": "例如：心血管循证医学\n临床预测模型",
        },
        {
            "id": "experience_inventory", "section": "workflow", "label": "除科研外，还有哪些经历可能值得写入简历？",
            "help": "可多选。这一步只帮助安排后续采集，不会直接写进简历。",
            "kind": "multi_choice", "required": False,
            "options": ["临床见习或轮转", "实习或工作", "校园组织与领导力", "志愿服务或社会实践", "其他项目", "目前没有其他经历"],
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
            if question["section"] == "workflow":
                continue
            evidence_index = question.get("evidence_index", index)
            items = value if question["kind"] in {"multiline_list", "multi_choice"} else [value]
            for item_index, item in enumerate(items, 1):
                records.append({
                    "evidence_id": f"profile_ev_{evidence_index:03d}_{item_index:02d}" if len(items) > 1 or question["kind"] in {"multiline_list", "multi_choice"} else f"profile_ev_{evidence_index:03d}",
                    "field": question["id"], "item_index": item_index,
                    "section": question["section"],
                    "source_text": cls._statement(question, item),
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
    def document_sections(cls, profile: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
        if profile.get("status") != "confirmed":
            return (
                {"name": None, "phone": None, "email": None, "location": None, "summary": None, "evidence_ids": []},
                [],
                {"awards": [], "languages": [], "certificates": [], "research_interests": [], "publications": []},
                [],
            )
        answers = profile.get("answers") or {}
        records = profile.get("profile_evidence_records") or []
        ids_by_section = {
            section: [item["evidence_id"] for item in records if item.get("section") == section]
            for section in ("basics", "education")
        }
        def item_evidence(field: str, item_index: int) -> list[str]:
            return [
                item["evidence_id"] for item in records
                if item.get("field") == field and item.get("item_index") == item_index
            ]
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
            "ranking_or_gpa": answers.get("ranking_or_gpa"),
            "highlights": answers.get("education_highlights") or [],
            "evidence_ids": ids_by_section["education"],
        }]
        extras = {
            "awards": [{
                "item_id": f"award_{index:03d}", "name": value,
                "issuer": None, "year": None,
                "evidence_ids": item_evidence("awards", index),
            } for index, value in enumerate(answers.get("awards") or [], 1)],
            "languages": [{
                "language": value, "level_or_score": None,
                "evidence_ids": item_evidence("languages", index),
            } for index, value in enumerate(answers.get("languages") or [], 1)],
            "certificates": [{
                "name": value, "category": "certificate", "level": None,
                "evidence_ids": item_evidence("certificates", index),
            } for index, value in enumerate(answers.get("certificates") or [], 1)],
            "research_interests": [{
                "name": value,
                "evidence_ids": item_evidence("research_interests", index),
            } for index, value in enumerate(answers.get("research_interests") or [], 1)],
            "publications": [{
                "item_id": f"publication_{index:03d}", "title": value,
                "venue": None, "status": "unknown", "author_position": None,
                "year": None, "evidence_ids": item_evidence("academic_outputs", index),
            } for index, value in enumerate(answers.get("academic_outputs") or [], 1)],
        }
        evidence = [{
            "evidence_id": item["evidence_id"], "statement": item["source_text"],
            "source_document_id": None, "source_locator": None,
            "status": "user_confirmed", "confirmed_at": None,
        } for item in records]
        return basics, education, extras, evidence

    @staticmethod
    def _normalize(question: dict[str, Any], value: Any) -> Any:
        if question["kind"] in {"multiline_list", "multi_choice"}:
            raw_items = value if isinstance(value, list) else str(value or "").splitlines()
            items = list(dict.fromkeys(re.sub(r"\s+", " ", str(item).strip()) for item in raw_items if str(item).strip()))
            if question["kind"] == "multi_choice":
                allowed = set(question.get("options") or [])
                if not set(items).issubset(allowed):
                    raise CandidateProfileInputError("经历盘点包含未提供的选项，请重新选择。")
                if "目前没有其他经历" in items and len(items) > 1:
                    raise CandidateProfileInputError("“目前没有其他经历”不能与其他选项同时选择。")
            if len(items) > 20:
                raise CandidateProfileInputError("单个模块最多填写 20 项，请保留最相关内容。")
            if any(len(item) > 200 for item in items):
                raise CandidateProfileInputError("单个条目过长，请保留正式名称和必要信息。")
            return items or None
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
