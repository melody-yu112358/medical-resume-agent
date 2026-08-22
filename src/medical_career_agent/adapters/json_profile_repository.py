from __future__ import annotations

import json
from pathlib import Path

from ..domain.career_models import (
    MedicalProfile,
    ProfileConstraints,
    ProfileEvidence,
)


class JsonMedicalProfileRepository:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        profiles = [self._load_file(path) for path in sorted(self.directory.glob("*.json"))]
        self._profiles = {profile.profile_id: profile for profile in profiles}

    def _load_file(self, path: Path) -> MedicalProfile:
        item = json.loads(path.read_text(encoding="utf-8"))
        constraints = item["constraints"]
        return MedicalProfile(
            profile_id=item["profile_id"],
            profile_type=item["profile_type"],
            education_field=item["education"]["field"],
            education_stage=item["education"]["stage"],
            evidence=tuple(
                ProfileEvidence(
                    evidence_id=evidence["evidence_id"],
                    statement=evidence["statement"],
                    capabilities=tuple(evidence.get("capabilities", [])),
                    confidence=evidence.get("confidence"),
                )
                for evidence in item["evidence"]
            ),
            constraints=ProfileConstraints(
                locations=tuple(constraints.get("locations", [])),
                weekly_learning_hours=constraints.get("weekly_learning_hours"),
                non_negotiables=tuple(constraints.get("non_negotiables", [])),
            ),
            unknowns=tuple(item.get("unknowns", [])),
        )

    def get(self, profile_id: str) -> MedicalProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise LookupError(f"unknown profile_id: {profile_id}") from exc

    def list(self) -> list[MedicalProfile]:
        return list(self._profiles.values())
