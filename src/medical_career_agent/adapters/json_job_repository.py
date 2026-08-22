from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from ..domain.models import JobPosting, SalaryEvidence, SourceRef


class JsonJobRepository:
    def __init__(self, path: str | Path, *, allow_multiple: bool = False) -> None:
        self.path = Path(path)
        self.allow_multiple = allow_multiple
        self._jobs = {job.job_id: job for job in self._load()}

    def _load(self) -> list[JobPosting]:
        return [job for record in self._iter_records() for job in (self._parse_record(record),)]

    def _iter_records(self) -> list[dict]:
        if self.path.is_dir():
            json_paths = sorted(self.path.glob("*.json"))
            if not json_paths:
                raise RuntimeError(f"directory has no json files: {self.path}")
            return [item for path in json_paths for item in json.loads(path.read_text(encoding="utf-8"))]

        if not self.path.exists():
            raise FileNotFoundError(f"job file not found: {self.path}")

        records = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError(f"job data must be a JSON array: {self.path}")

        if not self.allow_multiple:
            return records

        if self.path.name != "jobs.sample.json":
            return records

        return records

    def _parse_salary(self, item: dict) -> tuple[SalaryEvidence, str | None]:
        raw_salary = item.get("salary_raw")
        salary_blob = item.get("salary")
        if isinstance(salary_blob, dict):
            salary = SalaryEvidence(
                minimum=salary_blob.get("minimum"),
                maximum=salary_blob.get("maximum"),
                months_per_year=salary_blob.get("months_per_year"),
                currency=salary_blob.get("currency", "CNY"),
                period=salary_blob.get("period", "month"),
                raw_text=salary_blob.get("raw_text", "未公开"),
            )
            salary_text = salary_blob.get("raw_text")
            return salary, salary_text
        minimum, maximum = self._parse_salary_range_text(raw_salary) if raw_salary else (None, None)
        if minimum or maximum:
            salary = SalaryEvidence(
                minimum=minimum if isinstance(minimum, int) else int(minimum) if minimum is not None else None,
                maximum=maximum if isinstance(maximum, int) else int(maximum) if maximum is not None else None,
                raw_text=str(raw_salary),
            )
            return salary, raw_salary
        return SalaryEvidence(None, None, raw_text="未公开"), raw_salary

    @staticmethod
    def _parse_salary_range_text(raw_salary: str | None) -> tuple[int | None, int | None]:
        if not raw_salary:
            return None, None
        # 常见示例: "2-3万/月", "2.0-2.5万", "12000-16000"
        normalized = re.sub(r"\s+", "", str(raw_salary))
        m = re.search(r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)(?:万)?", normalized)
        if not m:
            return None, None
        low = float(m.group(1))
        high = float(m.group(2))
        if "万" in normalized:
            low *= 10000
            high *= 10000
        min_value = int(low) if low.is_integer() else int(low * 1000) / 1000
        max_value = int(high) if high.is_integer() else int(high * 1000) / 1000
        return min_value, max_value

    def _parse_source(self, item: dict) -> tuple[SourceRef, str | None]:
        source = item.get("source", {})
        if not isinstance(source, dict):
            source = {}
        collected = source.get("collected_at") or source.get("accessed_at")
        return (
            SourceRef(
                url=source.get("url", "未提供来源链接"),
                collected_at=date.fromisoformat(str(collected)) if collected else date.today(),
                label=source.get("label", source.get("type", "public_job_posting")),
            ),
            source.get("quality") or source.get("source_quality"),
        )

    @staticmethod
    def _coerce_tuple(value: object, *, fallback: str = "") -> tuple[str, ...]:
        if not value:
            return () if not fallback else (fallback,)
        if isinstance(value, str):
            return (value,)
        return tuple(str(item) for item in value)

    def _parse_record(self, item: dict) -> JobPosting:
        if not isinstance(item, dict):
            raise ValueError("Each job record must be an object")

        salary, salary_text = self._parse_salary(item)
        source, source_quality = self._parse_source(item)
        requirements = self._coerce_tuple(item.get("requirements"), fallback="")
        requirements = tuple(req for req in requirements if req)
        responsibilities = self._coerce_tuple(item.get("responsibilities"), fallback="")

        return JobPosting(
            job_id=str(item["job_id"]),
            title=str(item.get("title", "未提供岗位名")),
            company=str(item.get("company", "未提供公司名")),
            location=str(item.get("location", "未提供")),
            description=str(item.get("description", "")),
            requirements=tuple(req for req in requirements if req),
            salary=salary,
            source=source,
            synthetic=bool(item.get("synthetic", False)),
            employment_type=str(
                item.get("employment_type")
                or item.get("job_type")
                or item.get("type")
                or "未公开"
            ),
            experience=item.get("experience") or item.get("experience_years"),
            education=item.get("education") or item.get("education_requirements"),
            salary_raw=str(salary_text) if salary_text else None,
            verification_status=str(item.get("verification_status", "unknown")),
            career_name=str(item.get("career_name") or item.get("career") or item.get("career_id") or "未分类"),
            source_quality=source_quality,
            responsibilities=responsibilities if responsibilities else tuple(item.get("responsibilities") or item.get("tasks") or ()),
            raw_payload=item,
        )

    def get(self, job_id: str) -> JobPosting:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise LookupError(f"unknown job_id: {job_id}") from exc

    def list(self, *, location: str | None = None) -> list[JobPosting]:
        jobs = list(self._jobs.values())
        return [job for job in jobs if job.location == location] if location else jobs
