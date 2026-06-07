"""Fitness scoring that rewards CAPABILITY, not smallness.

The previous version's global optimum was "tiny standalone stub": it penalized
size, saturated capability at 2 new symbols, and graded correctness on the
coder's own tests. This version optimizes for what we actually want:

- correctness      : the change's tests pass in the jail.
- test_strength    : INDEPENDENT signal (mutation score) — do the tests actually
                     catch injected bugs? Defeats shallow self-grading.
- integration      : does the change import/compose the project's OWN modules,
                     rather than adding an isolated leaf?
- capability_gain  : NOVEL public capability, with a non-duplication penalty so
                     rebuilding something that already exists scores ~0.
- maintainability  : cohesion (has real functions, parses) — NOT brevity.
- security         : red team did not BLOCK.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

OWN_IMPORT = re.compile(r"(?:from|import)\s+ecnyss[\w.]*")


def build_registry(root: Path, exclude_paths: set[str]) -> tuple[set[str], set[str]]:
    """Return (existing public symbols, existing module stems) across ecnyss/,
    excluding the files being changed this cycle (so they count as new)."""
    symbols: set[str] = set()
    modules: set[str] = set()
    for p in (root / "ecnyss").rglob("*.py"):
        rel = str(p.relative_to(root))
        if rel in exclude_paths or "test" in p.name:
            continue
        modules.add(p.stem)
        try:
            for n in ast.walk(ast.parse(p.read_text(encoding="utf-8", errors="replace"))):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
                    symbols.add(n.name)
        except SyntaxError:
            continue
    return symbols, modules


def _public_symbols(content: str) -> set[str]:
    try:
        return {n.name for n in ast.walk(ast.parse(content))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and not n.name.startswith("_")}
    except SyntaxError:
        return set()


def score(report: dict[str, Any], files: list[dict[str, str]], redteam_blocked: bool,
          weights: dict[str, float], root: Path, mutation_score: float = 0.5) -> dict[str, float]:
    passed = bool(report.get("tests", {}).get("passed"))
    code_files = [f for f in files if f["path"].endswith(".py") and "test" not in f["path"]]
    changed_paths = {f["path"] for f in files}

    existing_syms, existing_mods = build_registry(root, changed_paths)

    # integration: own-module imports across the changed code files.
    own_imports = 0
    new_syms: set[str] = set()
    for f in code_files:
        own_imports += len(OWN_IMPORT.findall(f["content"]))
        new_syms |= _public_symbols(f["content"])
    integration = min(1.0, 0.2 + 0.4 * own_imports)  # 0->0.2, 1->0.6, 2+->1.0

    # capability_gain: novel public symbols, penalised for duplicating existing ones.
    novel = new_syms - existing_syms
    dup = new_syms & existing_syms
    dup_modules = {f for f in changed_paths if Path(f).stem in existing_mods and "test" not in f}
    novelty = 1.0 if not new_syms else len(novel) / len(new_syms)
    cap = min(1.0, 0.2 + 0.2 * len(novel)) * novelty   # needs ~4 novel symbols to max
    if dup_modules and not novel:           # rebuilding an existing module wholesale
        cap = min(cap, 0.15)

    # maintainability: cohesion, not brevity — parses + actually defines things.
    maint = 1.0 if new_syms else (0.6 if code_files else 0.4)

    s = {
        "correctness": 1.0 if passed else 0.0,
        "test_strength": round(max(0.0, min(1.0, mutation_score)), 3),
        "integration": round(integration, 3),
        "capability_gain": round(cap, 3),
        "maintainability": round(maint, 3),
        "security": 0.0 if redteam_blocked else 1.0,
    }
    return {k: s.get(k, 0.0) for k in weights}
