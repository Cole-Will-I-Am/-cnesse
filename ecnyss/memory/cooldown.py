"""Goal cooldown — stop the lab re-attacking a target that keeps failing.

Each rejection increments a counter for the target key; once it crosses the
threshold the target is "on cooldown" and surfaced to the Architect as something
to avoid, so cycles stop burning on the same thrice-rejected goal. A merge clears
the key.
"""
from __future__ import annotations

import json
from pathlib import Path


class Cooldown:
    def __init__(self, path: str | Path, threshold: int = 3):
        self.path = Path(path)
        self.threshold = threshold
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, int]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _save(self, d: dict[str, int]) -> None:
        self.path.write_text(json.dumps(d), encoding="utf-8")

    def record(self, key: str) -> None:
        if not key:
            return
        d = self._load()
        d[key] = d.get(key, 0) + 1
        self._save(d)

    def clear(self, key: str) -> None:
        d = self._load()
        if key in d:
            del d[key]
            self._save(d)

    def cooled(self) -> list[str]:
        return [k for k, v in self._load().items() if v >= self.threshold]
