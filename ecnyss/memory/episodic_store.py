"""Episodic memory — what happened in each cycle.

Derived from the hash chain (the single source of truth), so episodic memory
can never silently diverge from the audit ledger. Provides recent-cycle recall
and a compact summary for agent prompts, including which proposals were rejected
and why (so the lab learns from its own failures).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..protocol.hash_chain import HashChain


class EpisodicStore:
    def __init__(self, chain: HashChain):
        self.chain = chain

    def _payloads(self) -> list[dict[str, Any]]:
        out = []
        if self.chain.path.exists():
            for line in self.chain.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    out.append(json.loads(line)["payload"])
        return out

    def recent(self, n: int = 5) -> list[dict[str, Any]]:
        return self._payloads()[-n:]

    def failures(self, n: int = 5) -> list[dict[str, Any]]:
        return [p for p in self._payloads() if p.get("approval_state") == "rejected"][-n:]

    def stats(self) -> dict[str, int]:
        payloads = self._payloads()
        approved = sum(1 for p in payloads if p.get("approval_state") == "approved")
        rejected = sum(1 for p in payloads if p.get("approval_state") == "rejected")
        return {"total": len(payloads), "approved": approved, "rejected": rejected}

    def summary(self, n: int = 5) -> str:
        s = self.stats()
        lines = [f"Cycles: {s['total']} (approved {s['approved']}, rejected {s['rejected']})"]
        lines.append("Recent:")
        for p in self.recent(n):
            why = (p.get("provenance", {}) or {}).get("why", "")
            lines.append(f"  {p.get('cycle_id','?')} [{p.get('approval_state')}] {p.get('proposal','')[:80]} :: {why[:80]}")
        fails = self.failures(3)
        if fails:
            lines.append("Avoid repeating recent failures:")
            for p in fails:
                lines.append(f"  - {p.get('proposal','')[:90]}")
        return "\n".join(lines)
