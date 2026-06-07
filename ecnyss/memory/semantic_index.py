"""Semantic memory — stable facts about the codebase.

Each fact (module purpose + public API) is derived by AST from the actual
source and stamped with provenance: the file's current content hash as
source_ref, a confidence, and a revalidation deadline. On refresh, any fact
whose source hash changed is re-derived; stale facts are not trusted.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from ..protocol.canonical import sha256_hex
from .entry import MemoryEntry


class SemanticIndex:
    def __init__(self, root: str | Path, store_path: str | Path):
        self.root = Path(root).resolve()
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def _source_files(self) -> list[Path]:
        return [
            p for p in self.root.rglob("*.py")
            if ".git" not in p.parts and "state" not in p.parts and "tests" not in p.parts
        ]

    def _describe(self, path: Path) -> MemoryEntry:
        src = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(self.root))
        purpose, public = "", []
        try:
            tree = ast.parse(src)
            purpose = (ast.get_docstring(tree) or "").splitlines()[0] if ast.get_docstring(tree) else ""
            public = sorted(
                n.name for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and not n.name.startswith("_")
            )
        except SyntaxError:
            purpose = "(unparseable)"
        return MemoryEntry(
            key=rel,
            value={"purpose": purpose, "public_api": public},
            source_ref=sha256_hex({"src": src}),
            confidence=0.9 if purpose and purpose != "(unparseable)" else 0.4,
        )

    def refresh(self) -> dict[str, int]:
        existing = {e.key: e for e in self.load()}
        updated, unchanged = 0, 0
        entries = []
        for path in self._source_files():
            fresh = self._describe(path)
            prior = existing.get(fresh.key)
            if prior and prior.source_ref == fresh.source_ref and not prior.is_stale():
                entries.append(prior); unchanged += 1
            else:
                entries.append(fresh); updated += 1
        self.store_path.write_text(
            json.dumps([e.to_dict() for e in entries], indent=2), encoding="utf-8"
        )
        return {"updated": updated, "unchanged": unchanged, "total": len(entries)}

    def load(self) -> list[MemoryEntry]:
        if not self.store_path.exists():
            return []
        return [MemoryEntry.from_dict(d) for d in json.loads(self.store_path.read_text(encoding="utf-8"))]

    def summary(self) -> str:
        rows = []
        for e in self.load():
            if e.trusted():
                api = ", ".join(e.value.get("public_api", [])[:6])
                rows.append(f"  {e.key}: {e.value.get('purpose','')[:70]} | api: {api}")
        return "CODEBASE MAP (trusted facts):\n" + ("\n".join(rows) or "  (none)")
