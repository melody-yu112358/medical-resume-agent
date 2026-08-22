from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from ..domain.models import JobPosting
from .resume_diagnostor import SKILL_TERMS
from .resume_intake import ResumeIntakeService


@dataclass(frozen=True)
class InterviewPlan:
    job_id: str
    role: str
    focus_questions: tuple[str, ...]
    practice_cases: tuple[str, ...]
    self_introduction_template: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "role": self.role,
            "focus_questions": list(self.focus_questions),
            "practice_cases": list(self.practice_cases),
            "self_introduction_template": self.self_introduction_template,
        }


class InterviewCoachService:
    """Generate deterministic HR 面试问答预案（不调用 LLM）。"""

    def __init__(self, intake_service: ResumeIntakeService | None = None) -> None:
        self.intake_service = intake_service or ResumeIntakeService()

    def build_plan(self, *, resume_text: str, jd_text: str, job: JobPosting) -> InterviewPlan:
        if not resume_text.strip():
            raise ValueError("resume_text cannot be empty")
        if not jd_text.strip():
            raise ValueError("jd_text cannot be empty")

        intake = self.intake_service.analyze(resume_text=resume_text, jd_text=jd_text)
        missing = [m.requirement for m in intake.evidence_matches if m.gap_type]
        missing = missing[:6]

        questions = []
        for index, req in enumerate(missing, 1):
            questions.append(f"{index}. 你如何用医学训练中的具体经历证明：{req}？请补充情境-行动-结果。")

        # 基于岗位属性加入 2-3 个通用高频 HR 问题
        questions.extend(
            (
                "1. 为什么你会从医学出身转向这个方向？你做了哪些提前验证？",
                "2. 你认为转行第一阶段的 30/60/90 天目标是什么？",
                "3. 如何用一次小规模案例证明你能把临床/科研能力转化为业务价值？",
            )
        )

        # 去重并保留顺序
        focus_questions = tuple(OrderedDict.fromkeys(questions))

        skills = [k for k, terms in SKILL_TERMS.items() if any(t in resume_text.lower() for t in terms)]
        skills_str = "、".join(skills[:4]) if skills else "你的经验与表达能力"

        template = (
            f"我是医学背景的转行者，擅长{skills_str}。" 
            f"我的目标岗位是{job.title}，我能把问题拆解为：先确认证据边界，再给出可交付动作，" 
            f"以岗位要求中的‘{missing[0] if missing else '核心职责'}’为起点推进项目。"
        )

        cases = (
            "请讲一个你主导或参与的项目，从问题识别到执行复盘的完整过程。",
            "讲一次你如何处理与跨学科同事的分歧并推动结果落地。",
            "讲一个你的工作被纠正/否决后，你如何修正后再次验证。",
        )
        return InterviewPlan(
            job_id=job.job_id,
            role=job.title,
            focus_questions=focus_questions,
            practice_cases=cases,
            self_introduction_template=template,
        )
