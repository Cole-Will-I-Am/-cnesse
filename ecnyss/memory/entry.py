"""Auditable memory entry.

No ungrounded "belief" may influence a code change. Every fact carries its
source, a confidence, and a revalidation deadline — after which it must be
re-derived from the source of truth before it can be trusted again.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from typing import Any


def _utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class MemoryEntry:
    key: str
    value: Any
    source_ref: str                 # commit / file / cycle_id the fact came from
    confidence: float = 0.5         # 0..1
    created_at: str = field(default_factory=lambda: _utc().isoformat(timespec="seconds"))
    revalidate_after: str = field(
        default_factory=lambda: (_utc() + timedelta(days=7)).isoformat(timespec="seconds")
    )

    def is_stale(self, now: datetime | None = None) -> bool:
        now = now or _utc()
        try:
            return now >= datetime.fromisoformat(self.revalidate_after)
        except ValueError:
            return True

    def trusted(self) -> bool:
        """A fact is trustworthy only if grounded and not past revalidation."""
        return bool(self.source_ref) and self.confidence > 0.0 and not self.is_stale()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MemoryEntry":
        return cls(**{k: d[k] for k in d if k in cls.__dataclass_fields__})
