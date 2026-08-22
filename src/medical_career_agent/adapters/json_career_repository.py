from __future__ import annotations

import json
from pathlib import Path

from ..domain.career_models import (
    CareerRecord,
    CareerSource,
    MarketClaim,
)


def _load_claims(items: list[dict[str, object]] | None) -> tuple[MarketClaim, ...]:
    return tuple(
        MarketClaim(
            claim=str(item["claim"]),
            source_ids=tuple(str(value) for value in item["source_ids"]),
            claim_type=str(item["claim_type"]),
            confidence=item.get("confidence"),
        )
        for item in (items or [])
    )


class JsonCareerRepository:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        records = [self._load_file(path) for path in sorted(self.directory.glob("*.json"))]
        self._records = {record.career_id: record for record in records}

    def _load_file(self, path: Path) -> CareerRecord:
        item = json.loads(path.read_text(encoding="utf-8"))
        return CareerRecord(
            career_id=item["career_id"],
            name=item["name"],
            market=item["market"],
            summary=item.get("summary"),
            required_skills=_load_claims(item.get("required_skills")),
            medical_transferable_skills=_load_claims(
                item.get("medical_transferable_skills")
            ),
            work_environment=_load_claims(item.get("work_environment")),
            entry_barriers=_load_claims(item.get("entry_barriers")),
            validation_actions=tuple(item.get("validation_actions", [])),
            sources=tuple(
                CareerSource(
                    source_id=source["source_id"],
                    title=source["title"],
                    url=source["url"],
                    publisher=source["publisher"],
                    accessed_at=source["accessed_at"],
                )
                for source in item["sources"]
            ),
            review_status=item["review_status"],
        )

    def get(self, career_id: str) -> CareerRecord:
        try:
            return self._records[career_id]
        except KeyError as exc:
            raise LookupError(f"unknown career_id: {career_id}") from exc

    def list(self) -> list[CareerRecord]:
        return list(self._records.values())
