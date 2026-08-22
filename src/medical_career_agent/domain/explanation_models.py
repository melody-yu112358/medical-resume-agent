from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CareerExplanation:
    profile_id: str
    text: str
    model_role: str
    hypothesis_ids: tuple[str, ...]
    cited_evidence_ids: tuple[str, ...]
    quality_checks: tuple[str, ...]
    quality_gate_version: str = "career-explanation-gate-v0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
