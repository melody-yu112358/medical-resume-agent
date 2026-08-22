from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CareerTarget:
    career_id: str
    career_name: str
    summary: str
    requirements: tuple[str, ...]
    source_ids: tuple[str, ...]
    review_status: str
    generated_jd_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CareerTargetService:
    """Convert one sourced career card into a resume-target profile."""

    def build(self, career: object) -> CareerTarget:
        skills = tuple(item.claim for item in career.required_skills)
        if not skills:
            raise ValueError("career card has no required skills")
        source_ids = tuple(
            dict.fromkeys(
                source_id
                for claim in career.required_skills
                for source_id in claim.source_ids
            )
        )
        lines = [
            f"目标方向：{career.name}",
            f"岗位概述：{career.summary or '职业卡暂未提供概述'}",
            *(f"要求：{claim}" for claim in skills),
        ]
        return CareerTarget(
            career_id=career.career_id,
            career_name=career.name,
            summary=career.summary or "",
            requirements=skills,
            source_ids=source_ids,
            review_status=career.review_status,
            generated_jd_text="\n".join(lines),
        )

