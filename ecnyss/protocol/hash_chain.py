"""Append-only, hash-linked ledger of evolution records.

Every cycle artifact is appended as a block linking the previous block's hash,
forming a tamper-evident chain (genesis -> ... -> head). Any retroactive edit
breaks the chain and is detectable by `verify()`. This is the immutable spine
that makes Ecnyss auditable: the system can always answer "what happened, in
what order, and has anything been altered since."
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from .canonical import canonical_json, sha256_hex

GENESIS_PREV = "sha256:0" * 0 + "sha256:genesis"


class HashChain:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def head(self) -> str:
        last = None
        for block in self._iter_blocks():
            last = block
        return last["hash"] if last else GENESIS_PREV

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Append a payload as a new block; returns the sealed block."""
        prev = self.head()
        index = self.length()
        body = {"index": index, "prev_hash": prev, "payload": payload}
        block = {**body, "hash": sha256_hex(body)}
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(block))
        return block

    def length(self) -> int:
        return sum(1 for _ in self._iter_blocks())

    def verify(self) -> tuple[bool, str]:
        """Validate linkage and per-block hashes. Returns (ok, detail)."""
        prev = GENESIS_PREV
        idx = 0
        for block in self._iter_blocks():
            if block.get("index") != idx:
                return False, f"index mismatch at block {idx}: {block.get('index')}"
            if block.get("prev_hash") != prev:
                return False, f"broken link at block {idx}"
            body = {"index": block["index"], "prev_hash": block["prev_hash"], "payload": block["payload"]}
            if sha256_hex(body) != block.get("hash"):
                return False, f"hash mismatch at block {idx} (tampered)"
            prev = block["hash"]
            idx += 1
        return True, f"chain valid ({idx} blocks)"

    def _iter_blocks(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)
