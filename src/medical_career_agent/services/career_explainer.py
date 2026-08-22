from __future__ import annotations

import re

from ..domain.career_models import CareerComparisonRun
from ..domain.explanation_models import CareerExplanation
from ..ports.repositories import ModelGateway


class ModelOutputRejectedError(RuntimeError):
    pass


EXPLANATION_TASK = """
你是“未界”的语言解释层，不是职业决策者。请只依据输入 JSON，用中文解释
确定性职业比较结果。不得改变排序或证据覆盖率，不得添加用户经历、职业事实、
薪资、招聘数量或成功预测，不得进行人格判断、心理诊断或使用“最适合”“一定适合”
等判决语言。把每个方向称为“职业假设”。

输出纯文本或 Markdown。依次解释每个假设为什么值得验证、已有证据、反证/缺口、
未知信息和下一项行动。每个方向至少原样引用一个 supporting_evidence 中的
evidence_id。明确百分比只是证据覆盖率，不是适合度。职业卡为 draft 时必须提示
仍需人工复核。不要输出输入中不存在的 URL 或 source_id。
""".strip()


FORBIDDEN_OUTPUT = (
    "一定适合",
    "最适合",
    "保证就业",
    "保证成功",
    "成功率",
    "薪资预测",
    "薪资保证",
    "性格决定",
    "命中率",
)


class CareerExplanationService:
    def __init__(self, model: ModelGateway) -> None:
        self.model = model

    def explain(self, run: CareerComparisonRun) -> CareerExplanation:
        context = {
            "product_boundary": {
                "recommendations_are": "revisable career hypotheses",
                "coverage_is_not": "fit, personality, employability, salary, or success",
            },
            "comparison": run.to_dict(),
        }
        text = self.model.generate(task=EXPLANATION_TASK, context=context)
        cited_evidence_ids = self._validate(text, run)
        return CareerExplanation(
            profile_id=run.profile_id,
            text=text,
            model_role="language_explanation_only",
            hypothesis_ids=tuple(item.career_id for item in run.hypotheses),
            cited_evidence_ids=cited_evidence_ids,
            quality_checks=(
                "career_names_present",
                "profile_evidence_ids_present",
                "no_forbidden_verdict_language",
                "no_unapproved_percentages",
                "no_urls",
            ),
        )

    def _validate(
        self, text: str, run: CareerComparisonRun
    ) -> tuple[str, ...]:
        if len(text.strip()) < 80:
            raise ModelOutputRejectedError("model explanation is too short")
        forbidden = next((item for item in FORBIDDEN_OUTPUT if item in text), None)
        if forbidden:
            raise ModelOutputRejectedError(
                f"model explanation used forbidden verdict language: {forbidden}"
            )
        if "http://" in text or "https://" in text:
            raise ModelOutputRejectedError("model explanation added a URL")

        allowed_percentages = {
            f"{item.evidence_coverage_percent}%" for item in run.hypotheses
        }
        output_percentages = set(re.findall(r"\d+(?:\.\d+)?%", text))
        if output_percentages - allowed_percentages:
            raise ModelOutputRejectedError(
                "model explanation added an unapproved percentage"
            )

        cited: list[str] = []
        for hypothesis in run.hypotheses:
            if hypothesis.career_name not in text:
                raise ModelOutputRejectedError(
                    f"model explanation omitted career: {hypothesis.career_id}"
                )
            evidence_ids = [
                item.evidence_id for item in hypothesis.supporting_evidence
            ]
            cited_for_hypothesis = [item for item in evidence_ids if item in text]
            if not cited_for_hypothesis:
                raise ModelOutputRejectedError(
                    f"model explanation omitted profile evidence for: {hypothesis.career_id}"
                )
            cited.extend(cited_for_hypothesis)
        return tuple(dict.fromkeys(cited))
