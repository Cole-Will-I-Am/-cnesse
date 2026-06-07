"""Self-model and world-model — distinct knowledge the lab must not conflate.

SelfModel: what am I? which files define Ecnyss, what capabilities do I have.
WorldModel: what am I working on? target repo, goals, constraints, and mode
(self-improvement vs improving an external target). The orchestrator states the
active mode explicitly in every observation so an agent always knows whether it
is editing itself or a target.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .permission_model import PermissionModel


class SelfModel:
    def __init__(self, root: str | Path, permissions: PermissionModel):
        self.root = Path(root).resolve()
        self.permissions = permissions

    def defining_files(self) -> list[str]:
        return sorted(
            str(p.relative_to(self.root))
            for p in (self.root / "ecnyss").rglob("*.py")
        )

    def capabilities(self) -> dict[str, str]:
        return {k: v.value for k, v in self.permissions.scopes.items()}

    def summary(self) -> str:
        caps = ", ".join(f"{k}={v}" for k, v in self.capabilities().items())
        return (
            "SELF-MODEL: I am Ecnyss, an autonomous engineering lab.\n"
            f"  I am defined by {len(self.defining_files())} modules under ecnyss/.\n"
            f"  Capabilities: {caps}"
        )


class WorldModel:
    def __init__(self, config_path: str | Path):
        self.data: dict[str, Any] = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}

    @property
    def mode(self) -> str:
        return self.data.get("mode", "self")

    def summary(self) -> str:
        t = self.data.get("target", {})
        goals = "\n".join(f"    - {g}" for g in t.get("goals", []))
        cons = "\n".join(f"    - {c}" for c in t.get("constraints", []))
        scope = "MYSELF (self-improvement)" if self.mode == "self" else f"TARGET {t.get('repo','?')}"
        return (
            f"WORLD-MODEL: this cycle I am improving {scope}.\n"
            f"  Goals:\n{goals}\n  Constraints:\n{cons}"
        )
