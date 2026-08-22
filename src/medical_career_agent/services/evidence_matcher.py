from __future__ import annotations

from ..domain.models import JobPosting, MatchReport, ResumeProfile


REQUIREMENT_WEIGHT: dict[str, int] = {
    "必须": 3,
    "要求": 3,
    "学历": 3,
    "经验": 3,
    "核心": 2,
    "优先": 1,
    "加分": 1,
}


REQUIREMENT_TO_SKILLS: dict[str, tuple[str, ...]] = {
    "文献": ("文献检索", "医学写作"),
    "写作": ("医学写作",),
    "数据": ("数据分析",),
    "统计": ("数据分析",),
    "临床": ("临床研究", "医学知识"),
    "研究": ("临床研究", "文献检索"),
    "沟通": ("沟通表达", "项目协作"),
    "协作": ("项目协作", "沟通表达"),
    "医学": ("医学知识", "临床研究"),
    "合规": ("质量合规",),
    "gcp": ("质量合规", "临床研究"),
    "安全": ("质量合规", "医学知识"),
    "产品": ("产品思维", "项目协作"),
    "需求": ("产品思维", "沟通表达"),
}


class EvidenceMatcher:
    """Reproducible evidence matching; never invents resume facts."""

    def evaluate(self, profile: ResumeProfile, job: JobPosting) -> MatchReport:
        matched: list[str] = []
        missing: list[str] = []
        evidence = []
        criteria: list[dict[str, object]] = []
        total_weight = 0
        matched_weight = 0

        for requirement in job.requirements:
            expected = {
                skill
                for keyword, skills in REQUIREMENT_TO_SKILLS.items()
                if keyword in requirement.lower()
                for skill in skills
            }
            supporting = [item for item in profile.evidence if item.skill in expected]
            weight = next(
                (value for marker, value in REQUIREMENT_WEIGHT.items() if marker in requirement.lower()),
                1,
            )
            total_weight += weight
            if supporting:
                matched.append(requirement)
                evidence.extend(supporting)
                matched_weight += weight
                status = "matched"
                reason = "证据命中：简历支持该要求。"
            else:
                missing.append(requirement)
                status = "missing"
                reason = "未识别到可核实且与要求匹配的简历证据。"
            criteria.append(
                {
                    "requirement": requirement,
                    "weight": weight,
                    "status": status,
                    "score": weight if supporting else 0,
                    "matched_evidence": tuple(item.statement for item in supporting),
                    "reason": reason,
                }
            )

        total = len(job.requirements)
        score = round(100 * len(matched) / total) if total else 0
        weighted_score = round(100 * matched_weight / total_weight) if total_weight else score
        unique_evidence = tuple(dict.fromkeys(evidence))
        cautions = list(profile.unknowns)
        if job.synthetic:
            cautions.append("当前岗位为合成测试数据，不能用于市场结论")

        actions = tuple(f"补充能证明“{item}”的经历或作品" for item in missing[:3])
        return MatchReport(
            job_id=job.job_id,
            score=score,
            weighted_score=weighted_score,
            max_weight=total_weight,
            criterion_scores=tuple(criteria),
            matched_requirements=tuple(matched),
            missing_requirements=tuple(missing),
            supporting_evidence=unique_evidence,
            cautions=tuple(cautions),
            next_actions=actions,
        )

