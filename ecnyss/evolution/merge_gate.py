"""Merge gate — the promotion decision.

Combines the four independent signals into one verdict, enforcing
"no single agent proposes and approves its own evolution":
  1. Sandbox tests passed.
  2. Weighted objective score improves on baseline by >= merge_threshold.
  3. Red Team did not BLOCK.
  4. Maintainer (a different model than the Coder) approved.
  5. Permission policy allows the write scope.
All five must hold to merge; otherwise the change is recorded as rejected.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_objectives(config_path: str | Path) -> tuple[dict[str, float], float]:
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    return data.get("objectives", {}), float(data.get("merge_threshold", 0.0))


def score_change(report: dict[str, Any], action: str, redteam_blocked: bool,
                 weights: dict[str, float]) -> dict[str, float]:
    """Heuristic objective scoring from the sandbox report (0..1 per objective)."""
    tests = report.get("tests", {})
    passed = bool(tests.get("passed"))
    n_files = len(report.get("applied", []))
    diff_len = len(str(report.get("diff_hash", "")))  # placeholder magnitude

    scores = {
        "correctness": 1.0 if passed else 0.0,
        "test_coverage": 0.7 if any("test" in p for p in report.get("applied", [])) else 0.4,
        "maintainability": max(0.0, 1.0 - 0.1 * max(0, n_files - 1)),
        "simplicity": 1.0 if n_files <= 2 else 0.6,
        "capability_gain": 0.8 if action == "create" else 0.5,
        "security": 0.0 if redteam_blocked else 1.0,
    }
    return {k: scores.get(k, 0.0) for k in weights}


def weighted(scores: dict[str, float], weights: dict[str, float]) -> float:
    return round(sum(scores.get(k, 0.0) * w for k, w in weights.items()), 4)


def decide(*, tests_passed: bool, score: float, baseline: float, threshold: float,
           redteam_blocked: bool, maintainer_approved: bool,
           permission_ok: bool) -> tuple[bool, str]:
    if not permission_ok:
        return False, "permission policy denies write scope"
    if not tests_passed:
        return False, "sandbox tests failed"
    if redteam_blocked:
        return False, "red team BLOCK"
    if not maintainer_approved:
        return False, "maintainer rejected"
    if score < baseline + threshold:
        return False, f"score {score} below baseline {baseline}+{threshold}"
    return True, f"approved (score {score} >= {baseline}+{threshold})"
