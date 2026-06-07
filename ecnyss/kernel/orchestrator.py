"""Orchestrator — the cycle spine.

Phase 0 implements the auditable backbone only:
    observe -> propose -> record (pending)  [dry-run, no mutation]

Later phases extend this to the full pipeline:
    observe -> model -> propose -> simulate -> verify -> implement -> review
            -> merge -> learn
with cognition agents (planner/critic/verifier/red_team/maintainer) and the
sandboxed verify-before-promote executor. Crucially, the audit record is
written FIRST, so no capability can ever be added that bypasses the chain.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..protocol import CycleArtifact, HashChain, Provenance, Evidence, emit
from .permission_model import PermissionModel


class Orchestrator:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.permissions = PermissionModel(self.root / "config" / "permissions.yaml")
        self.objectives = yaml.safe_load(
            (self.root / "config" / "objectives.yaml").read_text(encoding="utf-8")
        ) or {}
        self.chain = HashChain(self.root / "state" / "evolution_chain.jsonl")

    def run_dry_cycle(self, proposal: str, why: str) -> dict[str, Any]:
        """Run one observe->propose->record cycle without mutating any source.

        Produces a grounded, pending audit artifact appended to the hash chain.
        This is the smallest end-to-end proof that the audit spine works.
        """
        basis_ref = self.chain.head()
        provenance = Provenance(
            why=why,
            objective_refs=["correctness"],
            evidence=[
                Evidence(
                    kind="dry_run",
                    source_ref=basis_ref,
                    detail="Phase 0 dry-run: no files mutated; record-only.",
                    confidence=1.0,
                )
            ],
        )
        artifact = CycleArtifact(
            proposal=proposal,
            basis_ref=basis_ref,
            provenance=provenance,
            approval_state="pending",
        )
        block = emit(self.chain, artifact)
        ok, detail = self.chain.verify()
        return {
            "cycle_id": artifact.cycle_id,
            "block_index": block["index"],
            "block_hash": block["hash"],
            "approval_state": artifact.approval_state,
            "chain_ok": ok,
            "chain_detail": detail,
        }
