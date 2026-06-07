"""Capability-based permission model.

Every action the system wants to take is checked against an explicit scope.
This is what makes autonomy safe: the executor physically cannot perform a
`forbidden` action, and `gated`/`human_required` actions are routed through the
sandbox + merge gate or a human approver. Default-deny for unknown scopes.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Decision(str, Enum):
    ALLOW = "allow"
    GATED = "gated"
    HUMAN_REQUIRED = "human_required"
    FORBIDDEN = "forbidden"


class PermissionError_(PermissionError):
    """Raised when a forbidden action is attempted."""


class PermissionModel:
    def __init__(self, config_path: str | Path):
        data: dict[str, Any] = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
        self.scopes: dict[str, Decision] = {
            k: Decision(v) for k, v in (data.get("permissions") or {}).items()
        }

    def check(self, scope: str) -> Decision:
        """Return the decision for a scope. Unknown scopes are default-deny."""
        return self.scopes.get(scope, Decision.FORBIDDEN)

    def require(self, scope: str) -> Decision:
        """Like check, but raise on forbidden so callers can't proceed."""
        decision = self.check(scope)
        if decision is Decision.FORBIDDEN:
            raise PermissionError_(f"action '{scope}' is forbidden by policy")
        return decision

    def autonomous_ok(self, scope: str) -> bool:
        """True only if the scope can be done without gating or a human."""
        return self.check(scope) is Decision.ALLOW
