"""Sandbox executor — verify before promote.

A proposed change is NEVER applied to the working tree. Instead we create an
isolated git worktree on a throwaway branch, apply the patch there, run the
test suite, and capture a diff hash + test report. The caller (merge gate) then
decides whether to promote the branch to a PR. The sandbox is always cleaned up.

    fork (worktree) -> patch -> test -> score -> [caller: PR/merge gate]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from ..protocol.canonical import sha256_hex


class Sandbox:
    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root).resolve()

    def _git(self, *args: str, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(cwd or self.repo_root), *args],
            capture_output=True, text=True, timeout=timeout,
        )

    def evaluate(self, files: list[dict[str, str]], action: str = "modify") -> dict[str, Any]:
        """Apply files in an isolated worktree, run tests, return a report."""
        branch = f"ecnyss/sandbox-{uuid.uuid4().hex[:8]}"
        wt_dir = Path(tempfile.mkdtemp(prefix="ecnyss_sbx_"))
        report: dict[str, Any] = {"branch": branch, "applied": [], "tests": {}, "diff_hash": None, "ok": False}
        try:
            add = self._git("worktree", "add", "-q", "-b", branch, str(wt_dir), "HEAD")
            if add.returncode != 0:
                report["error"] = f"worktree add failed: {add.stderr.strip()[:200]}"
                return report

            for f in files[:3]:  # max 3 files per cycle
                rel, content = f.get("path", ""), f.get("content", "")
                if not rel or content is None:
                    continue
                # Path safety: no escape, no dotfiles/secrets/CI.
                if ".." in rel or rel.startswith("/") or rel.startswith(".git") \
                   or "secret" in rel.lower() or rel.startswith(".github"):
                    report["error"] = f"unsafe path rejected: {rel}"
                    return report
                target = wt_dir / rel
                if action == "create" and target.exists():
                    report["error"] = f"create target exists: {rel}"
                    return report
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                report["applied"].append(rel)

            diff = self._git("add", "-A", cwd=wt_dir)
            diff_text = self._git("diff", "--cached", cwd=wt_dir).stdout
            report["diff_hash"] = sha256_hex({"diff": diff_text})

            report["tests"] = self._run_tests(wt_dir)
            report["ok"] = report["tests"].get("passed", False)
            return report
        finally:
            self._git("worktree", "remove", "--force", str(wt_dir))
            self._git("branch", "-D", branch)
            shutil.rmtree(wt_dir, ignore_errors=True)

    def _run_tests(self, wt_dir: Path) -> dict[str, Any]:
        tests_dir = wt_dir / "tests"
        if not tests_dir.exists() or not any(tests_dir.glob("test_*.py")):
            return {"passed": True, "detail": "no tests present", "ran": 0}
        proc = subprocess.run(
            ["python3", "-m", "unittest", "discover", "-s", "tests"],
            cwd=str(wt_dir), capture_output=True, text=True, timeout=240,
        )
        out = (proc.stdout + proc.stderr).strip()
        return {
            "passed": proc.returncode == 0,
            "detail": "\n".join(out.splitlines()[-25:]),
            "report_hash": sha256_hex({"out": out}),
        }
