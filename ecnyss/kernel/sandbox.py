"""Sandbox executor — verify before promote.

A proposed change is NEVER applied to the working tree. Instead we create an
isolated git worktree on a throwaway branch, apply the patch there, run the
test suite, and capture a diff hash + test report. The caller (merge gate) then
decides whether to promote the branch to a PR. The sandbox is always cleaned up.

    fork (worktree) -> patch -> test -> score -> [caller: PR/merge gate]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

import yaml

from ..protocol.canonical import sha256_hex


class Sandbox:
    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root).resolve()
        cfg_path = self.repo_root / "config" / "safety.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        self.iso = (cfg or {}).get("isolation", {}) or {}
        # Worktrees live OUTSIDE /tmp so PrivateTmp can give jailed tests a clean,
        # writable /tmp without hiding the worktree itself. World-traversable so
        # the dropped-privilege (nobody) test process can reach it.
        self.work_base = Path(self.iso.get("work_base", "/var/lib/ecnyss-sandbox"))
        try:
            self.work_base.mkdir(parents=True, exist_ok=True)
            self.work_base.chmod(0o777)
        except OSError:
            self.work_base = Path(tempfile.gettempdir())

    def _git(self, *args: str, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(cwd or self.repo_root), *args],
            capture_output=True, text=True, timeout=timeout,
        )

    def evaluate(self, files: list[dict[str, str]], action: str = "modify") -> dict[str, Any]:
        """Apply files in an isolated worktree, run tests, return a report."""
        branch = f"ecnyss/sandbox-{uuid.uuid4().hex[:8]}"
        wt_dir = Path(tempfile.mkdtemp(prefix="ecnyss_sbx_", dir=str(self.work_base)))
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

    def _test_cmd(self, wt_dir: Path) -> tuple[list[str], str]:
        """Build the test command. Prefer a systemd-run jail: non-root, no
        network, fs read-only outside the worktree, memory/CPU/time capped.
        Falls back to a bare subprocess only if systemd-run is unavailable."""
        inner = ["python3", "-m", "unittest", "discover", "-s", "tests"]
        if not (self.iso.get("enabled", True) and shutil.which("systemd-run")):
            return inner, "unisolated (systemd-run unavailable)"
        # nobody must be able to read/write the throwaway worktree.
        for p in wt_dir.rglob("*"):
            try:
                p.chmod(0o777)
            except OSError:
                pass
        wt_dir.chmod(0o777)
        cmd = [
            "systemd-run", "--pipe", "--wait", "--collect", "--quiet",
            f"--uid={self.iso.get('uid', 65534)}", f"--gid={self.iso.get('gid', 65534)}",
            "--property=ProtectSystem=strict", "--property=ProtectHome=yes",
            "--property=PrivateTmp=yes", "--property=NoNewPrivileges=yes",
            f"--property=MemoryMax={self.iso.get('memory_max', '1G')}",
            f"--property=CPUQuota={self.iso.get('cpu_quota', '90%')}",
            f"--property=TasksMax={self.iso.get('tasks_max', 256)}",
            f"--property=RuntimeMaxSec={self.iso.get('runtime_max_sec', 240)}",
            f"--property=ReadWritePaths={wt_dir}",
            f"--working-directory={wt_dir}",
            "--setenv=PYTHONDONTWRITEBYTECODE=1",
            "--setenv=ECNYSS_IN_JAIL=1",
        ]
        if self.iso.get("private_network", True):
            cmd.append("--property=PrivateNetwork=yes")
        return cmd + inner, "systemd-run jail (nobody, no-net, capped)"

    def _run_tests(self, wt_dir: Path) -> dict[str, Any]:
        tests_dir = wt_dir / "tests"
        if not tests_dir.exists() or not any(tests_dir.glob("test_*.py")):
            return {"passed": True, "detail": "no tests present", "ran": 0, "isolation": "n/a"}
        cmd, mode = self._test_cmd(wt_dir)
        try:
            proc = subprocess.run(cmd, cwd=str(wt_dir), capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            return {"passed": False, "detail": "tests timed out", "isolation": mode}
        out = (proc.stdout + proc.stderr).strip()
        return {
            "passed": proc.returncode == 0,
            "detail": "\n".join(out.splitlines()[-25:]),
            "report_hash": sha256_hex({"out": out}),
            "isolation": mode,
        }
