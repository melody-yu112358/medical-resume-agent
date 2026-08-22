from __future__ import annotations

from ..domain.models import ResumeEvidence, ResumeProfile


SKILL_TERMS: dict[str, tuple[str, ...]] = {
    "文献检索": ("文献检索", "pubmed", "检索策略", "系统综述"),
    "医学写作": ("论文", "医学写作", "科普", "撰写", "投稿"),
    "数据分析": ("数据分析", "统计", "spss", "r语言", "python", "excel"),
    "临床研究": ("临床研究", "课题", "试验", "研究方案", "病例"),
    "沟通表达": ("汇报", "宣讲", "沟通", "访谈", "组会"),
    "项目协作": ("协调", "项目", "合作", "推进", "团队"),
    "医学知识": ("临床", "医学", "疾病", "诊疗", "药物"),
    "质量合规": ("gcp", "sop", "合规", "伦理", "质控", "不良事件"),
    "产品思维": ("需求", "用户访谈", "产品", "原型", "迭代"),
}


class ResumeDiagnostor:
    """Extract only claims supported by the supplied resume text."""

    def diagnose(self, resume_text: str) -> ResumeProfile:
        normalized = resume_text.lower()
        evidence: list[ResumeEvidence] = []
        for skill, terms in SKILL_TERMS.items():
            matched = next((term for term in terms if term.lower() in normalized), None)
            if matched:
                evidence.append(
                    ResumeEvidence(
                        statement=f"简历中出现与“{skill}”相关的表述：{matched}",
                        skill=skill,
                    )
                )

        unknowns: list[str] = []
        if not any(char.isdigit() for char in resume_text):
            unknowns.append("经历中缺少可核实的数量、周期或结果")
        if not evidence:
            unknowns.append("尚未识别到目标岗位可用的能力证据")

        return ResumeProfile(
            raw_text=resume_text,
            skills=tuple(item.skill for item in evidence),
            evidence=tuple(evidence),
            unknowns=tuple(unknowns),
        )

