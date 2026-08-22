from __future__ import annotations

import json
from typing import Any

from ..domain.career_models import MedicalProfile, ProfileConstraints, ProfileEvidence
from ..domain.profile_draft_models import MedicalProfileDraft, ProfileEvidenceDraft
from ..ports.repositories import ModelGateway
from .career_comparator import CAPABILITY_GROUPS


class ProfileDraftInputError(ValueError):
    pass


class ProfileDraftOutputRejectedError(RuntimeError):
    pass


ALLOWED_PROFILE_CAPABILITIES = tuple(
    sorted(
        {
            capability
            for group in CAPABILITY_GROUPS.values()
            for capability in group.profile_terms
        }
    )
)


PROFILE_DRAFT_TASK = """
你是“未界”的画像证据提取层，不是职业推荐者。请只根据 user_input.experience_text
抽取用户明确描述过的行动证据，并返回一个 JSON 对象，不要输出 Markdown 或解释文字。

JSON 格式：
{
  "evidence": [
    {
      "source_quote": "从 experience_text 逐字复制的一段连续原文",
      "capabilities": ["只能从 allowed_capabilities 选择"],
      "confidence": 0.0
    }
  ],
  "unknowns": ["仅记录仍缺少、需要用户补充的信息"],
  "follow_up_question": "一个最值得继续追问的问题，或 null"
}

规则：
1. source_quote 必须是用户原文中逐字存在的连续片段，不得改写或补充结果。
2. 学历、论文名称或项目名称本身不是能力证据；必须有用户实际做过的动作。
3. capabilities 只能使用 allowed_capabilities，最多为一条证据选择 5 项。
4. 不推断人格、职业适合度、就业结果、薪资或用户没有表达的经历。
5. 信息不足时少提取或提出一个追问，不要为了凑数而编造。
6. 最多返回 6 条证据和 5 条 unknowns。
""".strip()


class ProfileDraftService:
    def __init__(self, model: ModelGateway) -> None:
        self.model = model

    def draft(
        self,
        *,
        education_field: str,
        education_stage: str,
        experience_text: str,
        locations: tuple[str, ...] = (),
        weekly_learning_hours: float | None = None,
        non_negotiables: tuple[str, ...] = (),
        consent_confirmed: bool = False,
    ) -> MedicalProfileDraft:
        field = education_field.strip()
        stage = education_stage.strip()
        source_text = experience_text.strip()
        if not consent_confirmed:
            raise ProfileDraftInputError("consent_confirmed must be true")
        if not field or not stage:
            raise ProfileDraftInputError("education field and stage are required")
        if len(source_text) < 30:
            raise ProfileDraftInputError(
                "experience_text must contain at least 30 characters"
            )
        if len(source_text) > 5000:
            raise ProfileDraftInputError(
                "experience_text must contain at most 5000 characters"
            )
        if weekly_learning_hours is not None and not 0 <= weekly_learning_hours <= 168:
            raise ProfileDraftInputError(
                "weekly_learning_hours must be between 0 and 168"
            )

        raw_output = self.model.generate(
            task=PROFILE_DRAFT_TASK,
            context={
                "allowed_capabilities": ALLOWED_PROFILE_CAPABILITIES,
                "user_input": {
                    "education_field": field,
                    "education_stage": stage,
                    "experience_text": source_text,
                },
            },
        )
        parsed = self._parse_output(raw_output)
        evidence = self._validated_evidence(parsed.get("evidence"), source_text)
        unknowns = self._validated_strings(
            parsed.get("unknowns", []), field_name="unknowns", maximum=5
        )
        follow_up_question = parsed.get("follow_up_question")
        if follow_up_question is not None:
            if not isinstance(follow_up_question, str) or not follow_up_question.strip():
                raise ProfileDraftOutputRejectedError(
                    "follow_up_question must be a non-empty string or null"
                )
            follow_up_question = follow_up_question.strip()
            if len(follow_up_question) > 200:
                raise ProfileDraftOutputRejectedError(
                    "follow_up_question is too long"
                )

        return MedicalProfileDraft(
            profile_id="session-profile-draft",
            education_field=field,
            education_stage=stage,
            evidence=evidence,
            locations=self._clean_user_strings(locations),
            weekly_learning_hours=weekly_learning_hours,
            non_negotiables=self._clean_user_strings(non_negotiables),
            unknowns=unknowns,
            follow_up_question=follow_up_question,
            consent_recorded=True,
        )

    def _parse_output(self, raw_output: str) -> dict[str, Any]:
        text = raw_output.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProfileDraftOutputRejectedError(
                "model profile draft is not valid JSON"
            ) from exc
        if not isinstance(parsed, dict):
            raise ProfileDraftOutputRejectedError(
                "model profile draft must be a JSON object"
            )
        return parsed

    def _validated_evidence(
        self, value: object, source_text: str
    ) -> tuple[ProfileEvidenceDraft, ...]:
        if not isinstance(value, list) or not 1 <= len(value) <= 6:
            raise ProfileDraftOutputRejectedError(
                "model profile draft must contain 1 to 6 evidence items"
            )
        drafts: list[ProfileEvidenceDraft] = []
        seen_quotes: set[str] = set()
        for index, item in enumerate(value, 1):
            if not isinstance(item, dict):
                raise ProfileDraftOutputRejectedError("evidence item must be an object")
            quote = item.get("source_quote")
            if not isinstance(quote, str) or len(quote.strip()) < 8:
                raise ProfileDraftOutputRejectedError(
                    "every evidence item needs a source_quote"
                )
            quote = quote.strip()
            if quote not in source_text:
                raise ProfileDraftOutputRejectedError(
                    "model evidence quote is not present in user input"
                )
            if quote in seen_quotes:
                raise ProfileDraftOutputRejectedError(
                    "model profile draft contains duplicate evidence"
                )
            seen_quotes.add(quote)

            capabilities = item.get("capabilities")
            if not isinstance(capabilities, list) or not 1 <= len(capabilities) <= 5:
                raise ProfileDraftOutputRejectedError(
                    "every evidence item needs 1 to 5 capabilities"
                )
            cleaned_capabilities = tuple(
                dict.fromkeys(
                    capability.strip()
                    for capability in capabilities
                    if isinstance(capability, str) and capability.strip()
                )
            )
            if len(cleaned_capabilities) != len(capabilities) or any(
                capability not in ALLOWED_PROFILE_CAPABILITIES
                for capability in cleaned_capabilities
            ):
                raise ProfileDraftOutputRejectedError(
                    "model profile draft used an unsupported capability"
                )

            confidence = item.get("confidence")
            if confidence is not None and (
                isinstance(confidence, bool)
                or not isinstance(confidence, (int, float))
                or not 0 <= float(confidence) <= 1
            ):
                raise ProfileDraftOutputRejectedError(
                    "evidence confidence must be between 0 and 1"
                )
            drafts.append(
                ProfileEvidenceDraft(
                    evidence_id=f"intake-evidence-{index:02d}",
                    source_quote=quote,
                    capabilities=cleaned_capabilities,
                    confidence=float(confidence) if confidence is not None else None,
                )
            )
        return tuple(drafts)

    def _validated_strings(
        self, value: object, *, field_name: str, maximum: int
    ) -> tuple[str, ...]:
        if not isinstance(value, list) or len(value) > maximum:
            raise ProfileDraftOutputRejectedError(
                f"{field_name} must be an array with at most {maximum} items"
            )
        cleaned = self._clean_user_strings(tuple(value))
        if len(cleaned) != len(value) or any(len(item) > 200 for item in cleaned):
            raise ProfileDraftOutputRejectedError(f"invalid {field_name}")
        return cleaned

    @staticmethod
    def _clean_user_strings(value: tuple[object, ...]) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                item.strip()
                for item in value
                if isinstance(item, str) and item.strip()
            )
        )


def confirmed_profile_from_payload(payload: object) -> MedicalProfile:
    if not isinstance(payload, dict):
        raise ProfileDraftInputError("profile must be an object")
    if payload.get("profile_confirmed") is not True:
        raise ProfileDraftInputError("profile_confirmed must be true")
    if payload.get("consent_recorded") is not True:
        raise ProfileDraftInputError("consent_recorded must be true")

    education = payload.get("education")
    if not isinstance(education, dict):
        raise ProfileDraftInputError("profile education is required")
    field = str(education.get("field", "")).strip()
    stage = str(education.get("stage", "")).strip()
    if not field or not stage:
        raise ProfileDraftInputError("profile education field and stage are required")

    evidence_payload = payload.get("evidence")
    if not isinstance(evidence_payload, list) or not 1 <= len(evidence_payload) <= 6:
        raise ProfileDraftInputError("confirmed profile needs 1 to 6 evidence items")
    evidence: list[ProfileEvidence] = []
    for index, item in enumerate(evidence_payload, 1):
        if not isinstance(item, dict) or item.get("confirmed") is not True:
            raise ProfileDraftInputError("every profile evidence item must be confirmed")
        statement = str(item.get("source_quote", "")).strip()
        capabilities_payload = item.get("capabilities")
        if not statement or not isinstance(capabilities_payload, list):
            raise ProfileDraftInputError("confirmed evidence is incomplete")
        if len(statement) > 800:
            raise ProfileDraftInputError("confirmed evidence quote is too long")
        capabilities = tuple(
            dict.fromkeys(
                str(capability).strip()
                for capability in capabilities_payload
                if str(capability).strip()
            )
        )
        if not 1 <= len(capabilities) <= 5 or any(
            capability not in ALLOWED_PROFILE_CAPABILITIES
            for capability in capabilities
        ):
            raise ProfileDraftInputError("confirmed evidence has unsupported capabilities")
        confidence = item.get("confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (TypeError, ValueError) as exc:
                raise ProfileDraftInputError("invalid evidence confidence") from exc
            if not 0 <= confidence <= 1:
                raise ProfileDraftInputError("invalid evidence confidence")
        evidence.append(
            ProfileEvidence(
                evidence_id=f"confirmed-evidence-{index:02d}",
                statement=statement,
                capabilities=capabilities,
                confidence=confidence,
            )
        )

    constraints = payload.get("constraints", {})
    if not isinstance(constraints, dict):
        raise ProfileDraftInputError("profile constraints must be an object")
    weekly_learning_hours = constraints.get("weekly_learning_hours")
    if weekly_learning_hours is not None:
        try:
            weekly_learning_hours = float(weekly_learning_hours)
        except (TypeError, ValueError) as exc:
            raise ProfileDraftInputError("invalid weekly learning hours") from exc
        if not 0 <= weekly_learning_hours <= 168:
            raise ProfileDraftInputError("invalid weekly learning hours")

    unknowns = payload.get("unknowns", [])
    cleaned_unknowns = _clean_payload_strings(unknowns)
    if len(cleaned_unknowns) > 5 or any(len(item) > 200 for item in cleaned_unknowns):
        raise ProfileDraftInputError("profile unknowns are invalid")
    return MedicalProfile(
        profile_id="session-confirmed-profile",
        profile_type="consented",
        education_field=field,
        education_stage=stage,
        evidence=tuple(evidence),
        constraints=ProfileConstraints(
            locations=_clean_payload_strings(constraints.get("locations", [])),
            weekly_learning_hours=weekly_learning_hours,
            non_negotiables=_clean_payload_strings(
                constraints.get("non_negotiables", [])
            ),
        ),
        unknowns=cleaned_unknowns,
    )


def _clean_payload_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ProfileDraftInputError("expected an array of strings")
    cleaned = tuple(
        dict.fromkeys(
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        )
    )
    if len(cleaned) != len(value):
        raise ProfileDraftInputError("expected non-empty strings")
    return cleaned
