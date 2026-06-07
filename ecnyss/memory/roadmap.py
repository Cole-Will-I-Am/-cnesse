"""Strategic memory — long-term roadmap and lessons.

Versioned, append-mostly store of priorities and lessons learned. Lessons are
distilled from rejected cycles so the lab does not repeat mistakes. Priorities
steer the Architect toward durable direction rather than cycle-to-cycle drift.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Roadmap:
    def __init__(self, store_path: str | Path):
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Any]:
        if self.store_path.exists():
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        return {"version": 0, "priorities": [], "lessons": []}

    def _save(self, data: dict[str, Any]) -> None:
        data["version"] = data.get("version", 0) + 1
        data["updated_at"] = _utc()
        self.store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_lesson(self, lesson: str, source_ref: str) -> None:
        data = self._load()
        if not any(l["lesson"] == lesson for l in data["lessons"]):
            data["lessons"].append({"lesson": lesson, "source_ref": source_ref, "at": _utc()})
            data["lessons"] = data["lessons"][-50:]
            self._save(data)

    def set_priorities(self, priorities: list[str]) -> None:
        data = self._load()
        data["priorities"] = priorities[:10]
        self._save(data)

    def summary(self) -> str:
        data = self._load()
        pri = "\n".join(f"  - {p}" for p in data.get("priorities", [])) or "  (none set)"
        les = "\n".join(f"  - {l['lesson']}" for l in data.get("lessons", [])[-5:]) or "  (none)"
        return f"STRATEGIC PRIORITIES:\n{pri}\nLESSONS:\n{les}"
