"""Babel-compatible cycle artifact — Babel is protocol law, Ecnyss the executor.

Every cycle emits one of these records to the hash chain. The schema follows
the v2 spec: basis_ref, proposal, diff_hash, test_result_hash, approval_state,
rollback_ref — plus grounded provenance. No code change is legitimate without a
corresponding approved artifact in the chain.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .canonical import sha256_hex
from .hash_chain import HashChain
from .provenance import Provenance

APPROVAL_STATES = ("pending", "approved", "rejected")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CycleArtifact:
    proposal: str
    basis_ref: str                          # chain head / git ref the cycle builds on
    provenance: Provenance
    cycle_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    diff_hash: str | None = None            # sha256 of the staged diff
    test_result_hash: str | None = None     # sha256 of the test report
    score: dict[str, float] = field(default_factory=dict)  # objective -> value
    approval_state: str = "pending"
    rollback_ref: str | None = None         # git ref to restore on revert
    created_at: str = field(default_factory=_utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "basis_ref": self.basis_ref,
            "proposal": self.proposal,
            "provenance": self.provenance.to_dict(),
            "diff_hash": self.diff_hash,
            "test_result_hash": self.test_result_hash,
            "score": self.score,
            "approval_state": self.approval_state,
            "rollback_ref": self.rollback_ref,
            "created_at": self.created_at,
        }

    def artifact_hash(self) -> str:
        return sha256_hex(self.to_dict())


def emit(chain: HashChain, artifact: CycleArtifact) -> dict[str, Any]:
    """Validate provenance + approval state, then append to the chain."""
    if artifact.approval_state not in APPROVAL_STATES:
        raise ValueError(f"invalid approval_state: {artifact.approval_state}")
    grounded, reason = artifact.provenance.is_grounded()
    if not grounded:
        raise ValueError(f"provenance not grounded: {reason}")
    return chain.append(artifact.to_dict())
