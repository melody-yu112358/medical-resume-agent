from __future__ import annotations

from typing import Protocol

from ..domain.career_models import CareerRecord, MedicalProfile
from ..domain.models import JobPosting


class JobRepository(Protocol):
    def get(self, job_id: str) -> JobPosting: ...

    def list(self, *, location: str | None = None) -> list[JobPosting]: ...


class CareerRepository(Protocol):
    def get(self, career_id: str) -> CareerRecord: ...

    def list(self) -> list[CareerRecord]: ...


class MedicalProfileRepository(Protocol):
    def get(self, profile_id: str) -> MedicalProfile: ...

    def list(self) -> list[MedicalProfile]: ...


class ModelGateway(Protocol):
    """Optional LLM boundary. Core scoring must not depend on it."""

    def generate(self, *, task: str, context: dict[str, object]) -> str: ...


class SessionRepository(Protocol):
    def create(self, session_id: str | None = None) -> str: ...

    def get(self, session_id: str) -> dict[str, object]: ...

    def update(self, session_id: str, *, state: dict[str, object] | None = None) -> dict[str, object]: ...

    def append_event(self, session_id: str, event: dict[str, object]) -> dict[str, object]: ...

    def list_sessions(self) -> list[dict[str, str]]: ...
