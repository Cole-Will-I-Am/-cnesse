"""Fitness scoring with real signal.

Replaces flat heuristics with measured signals so "improve yourself" is
grounded, not gameable by adding a 3-line stub:
- correctness     : tests pass in the jail.
- test_coverage   : change in number of tests actually run vs the repo baseline.
- maintainability : avg function size of changed non-test code (smaller better).
- simplicity      : net size of the change (smaller better).
- capability_gain : net new public symbols in changed non-test modules.
- security        : red team did not BLOCK.
Each is 0..1; the merge gate combines them with the configured weights.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


def baseline_test_count(root: Path) -> int:
    """Count test functions currently in tests/ (cheap coverage baseline)."""
    n = 0
    tdir = root / "tests"
    if not tdir.exists():
        return 0
    for p in tdir.glob("test_*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            n += sum(1 for x in ast.walk(tree)
                     if isinstance(x, ast.FunctionDef) and x.name.startswith("test"))
        except SyntaxError:
            continue
    return n


def _tests_run(detail: str) -> int:
    m = re.search(r"Ran (\d+) test", detail or "")
    return int(m.group(1)) if m else 0


def _avg_func_len(files: list[dict[str, str]]) -> float:
    lengths = []
    for f in files:
        if "test" in f["path"] or not f["path"].endswith(".py"):
            continue
        try:
            tree = ast.parse(f["content"])
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lengths.append(len(node.body))
    return sum(lengths) / len(lengths) if lengths else 0.0


def _new_public_symbols(root: Path, files: list[dict[str, str]]) -> int:
    gained = 0
    for f in files:
        if "test" in f["path"] or not f["path"].endswith(".py"):
            continue
        try:
            new = {n.name for n in ast.walk(ast.parse(f["content"]))
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                   and not n.name.startswith("_")}
        except SyntaxError:
            continue
        old: set[str] = set()
        fp = root / f["path"]
        if fp.exists():
            try:
                old = {n.name for n in ast.walk(ast.parse(fp.read_text(encoding="utf-8", errors="replace")))
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                       and not n.name.startswith("_")}
            except SyntaxError:
                pass
        gained += len(new - old)
    return gained


def score(report: dict[str, Any], files: list[dict[str, str]], redteam_blocked: bool,
          weights: dict[str, float], root: Path, baseline_tests: int) -> dict[str, float]:
    tests = report.get("tests", {})
    passed = bool(tests.get("passed"))
    ran = _tests_run(tests.get("detail", ""))
    avg_len = _avg_func_len(files)
    total_size = sum(len(f.get("content", "")) for f in files)
    gained = _new_public_symbols(root, files)

    cov = 1.0 if (passed and ran > baseline_tests) else (0.6 if ran == baseline_tests else 0.2)
    maint = 1.0 if avg_len <= 15 else max(0.2, 1.0 - (avg_len - 15) / 50.0)
    simp = 1.0 if total_size <= 2000 else max(0.2, 1.0 - (total_size - 2000) / 12000.0)
    cap = min(1.0, 0.5 + 0.25 * gained) if gained > 0 else 0.3

    s = {
        "correctness": 1.0 if passed else 0.0,
        "test_coverage": round(cov, 3),
        "maintainability": round(maint, 3),
        "simplicity": round(simp, 3),
        "capability_gain": round(cap, 3),
        "security": 0.0 if redteam_blocked else 1.0,
    }
    return {k: s.get(k, 0.0) for k in weights}
