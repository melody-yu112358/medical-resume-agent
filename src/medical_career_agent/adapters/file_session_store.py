from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path

from ..ports.repositories import SessionRepository


class FileSessionStore(SessionRepository):
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_session_id(session_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id):
            raise ValueError("session_id contains unsupported characters")
        return session_id

    def _path(self, session_id: str) -> Path:
        return self.directory / f"{self._validate_session_id(session_id)}.json"

    def create(self, session_id: str | None = None) -> str:
        resolved = session_id or str(uuid.uuid4())
        path = self._path(resolved)
        if path.exists():
            raise FileExistsError(f"会话已存在: {resolved}")
        payload = {
            "session_id": resolved,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "events": [],
            "state": {},
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return resolved

    def get(self, session_id: str) -> dict[str, object]:
        path = self._path(session_id)
        if not path.exists():
            raise LookupError(f"unknown session_id: {session_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def update(self, session_id: str, *, state: dict[str, object] | None = None) -> dict[str, object]:
        payload = self.get(session_id)
        if state is not None:
            current = payload.get("state", {})
            if not isinstance(current, dict):
                current = {}
            current.update(state)
            payload["state"] = current
        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        path = self._path(session_id)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def append_event(self, session_id: str, event: dict[str, object]) -> dict[str, object]:
        payload = self.get(session_id)
        events = payload.get("events")
        if not isinstance(events, list):
            events = []
        events.append(
            {
                **event,
                "ts": datetime.now().isoformat(timespec="seconds"),
            }
        )
        payload["events"] = events
        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        path = self._path(session_id)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def list_sessions(self) -> list[dict[str, str]]:
        result = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                result.append(
                    {
                        "session_id": str(raw.get("session_id")),
                        "created_at": str(raw.get("created_at", "")),
                        "updated_at": str(raw.get("updated_at", "")),
                    }
                )
            except (OSError, json.JSONDecodeError):
                continue
        return result

    def delete(self, session_id: str) -> bool:
        """Delete one validated local session file; return whether it existed."""
        path = self._path(session_id)
        if not path.exists():
            return False
        path.unlink()
        return True
