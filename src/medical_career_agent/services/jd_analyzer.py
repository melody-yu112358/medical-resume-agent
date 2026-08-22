from __future__ import annotations

import re

from ..domain.models import JobPosting, SalaryEvidence, SourceRef
from datetime import date


class JdAnalyzer:
    """Turn user-supplied JD text into traceable requirement lines."""

    def analyze(self, *, jd_text: str, title: str = "用户粘贴的目标岗位") -> JobPosting:
        if not jd_text.strip():
            raise ValueError("jd_text cannot be empty")

        fragments = re.split(r"[\n；;。]+|(?=\d+[.、])", jd_text)
        requirements = tuple(
            dict.fromkeys(
                cleaned
                for part in fragments
                if (cleaned := re.sub(r"^[-•*\s\d.、]+", "", part).strip())
            )
        )[:12]
        if not requirements:
            requirements = (jd_text.strip(),)

        return JobPosting(
            job_id="user-supplied-jd",
            title=title.strip() or "用户粘贴的目标岗位",
            company="用户未提供",
            location="用户未提供",
            description=jd_text.strip(),
            requirements=requirements,
            salary=SalaryEvidence(None, None, raw_text="用户未提供"),
            source=SourceRef(
                url="user-input://jd",
                collected_at=date.today(),
                label="user_supplied_jd",
            ),
            synthetic=False,
        )

