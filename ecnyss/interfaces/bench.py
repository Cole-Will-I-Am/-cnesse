"""Benchmark runner — scores the held-out bench/ suite and records the trajectory.

Independent of the coder's self-written tests: bench/ is protected and invisible
to the lab. Each run appends a point to state/benchmark.jsonl so "smarter" is a
measurable number over time, not vibes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    bench_dir = root / "bench"
    if not bench_dir.exists():
        return {"score": None, "reason": "no bench/"}
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "bench", "-p", "bench_*.py"],
        cwd=str(root), capture_output=True, text=True,
        env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin"}, timeout=120,
    )
    out = proc.stdout + proc.stderr
    ran = int(m.group(1)) if (m := re.search(r"Ran (\d+) test", out)) else 0
    fails = len(re.findall(r"^FAIL:", out, re.M))
    errs = len(re.findall(r"^ERROR:", out, re.M))
    passed = max(0, ran - fails - errs)
    score = round(passed / ran, 4) if ran else 0.0

    # Repo capability metrics (independent of bench).
    from ..evolution.fitness import build_registry
    symbols, modules = build_registry(root, set())

    point = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "score": score, "passed": passed, "total": ran,
        "modules": len(modules), "symbols": len(symbols),
    }
    log = root / "state" / "benchmark.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(point) + "\n")
    return point


def history(root: str | Path, n: int = 10) -> list[dict[str, Any]]:
    log = Path(root) / "state" / "benchmark.jsonl"
    if not log.exists():
        return []
    return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()][-n:]
