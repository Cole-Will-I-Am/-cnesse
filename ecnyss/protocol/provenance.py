"""Provenance: the justification attached to every change.

Enforces the prime directive — for every change the system must answer
"why did I do this?" and "what evidence justified it?". A proposal without
grounded provenance is rejected before it can reach a sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Evidence:
    """A single grounded justification item."""
    kind: str               # e.g. "test", "static_analysis", "metric", "spec_ref"
    source_ref: str         # commit / file / objective the evidence comes from
    detail: str
    confidence: float = 0.5  # 0..1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Provenance:
    why: str                              # human-readable rationale
    objective_refs: list[str] = field(default_factory=list)  # which objectives this serves
    evidence: list[Evidence] = field(default_factory=list)

    def is_grounded(self) -> tuple[bool, str]:
        if not self.why.strip():
            return False, "missing rationale (why)"
        if not self.evidence:
            return False, "no evidence attached"
        if not self.objective_refs:
            return False, "change serves no declared objective"
        return True, "grounded"

    def to_dict(self) -> dict[str, Any]:
        return {
            "why": self.why,
            "objective_refs": self.objective_refs,
            "evidence": [e.to_dict() for e in self.evidence],
        }
