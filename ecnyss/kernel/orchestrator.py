"""Orchestrator — the cycle spine and full evolve pipeline.

    observe -> architect -> planner -> coder -> SANDBOX(test) -> red team
            -> score -> maintainer -> merge gate -> promote(branch/PR) -> record

Invariants:
- The audit artifact is emitted every cycle (approved or rejected).
- No mutation ever lands on `main`; approved changes go to a branch + PR.
- No single agent both proposes and approves (coder != maintainer != red team).
- Permission policy is checked before any write scope.
"""
from __future__ import annotations

import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

import yaml

from ..protocol import CycleArtifact, HashChain, Provenance, Evidence, emit
from ..cognition.agent import Agent, load_registry, extract_json
from .permission_model import PermissionModel, Decision
from .sandbox import Sandbox
from ..evolution import merge_gate


class Orchestrator:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.permissions = PermissionModel(self.root / "config" / "permissions.yaml")
        self.objectives, self.merge_threshold = merge_gate.load_objectives(self.root / "config" / "objectives.yaml")
        self.chain = HashChain(self.root / "state" / "evolution_chain.jsonl")
        self.sandbox = Sandbox(self.root)
        registry, ollama_url = load_registry(self.root / "config" / "models.yaml")
        self.agents = {role: Agent(role, registry, ollama_url) for role in registry}

    # ---- helpers -----------------------------------------------------------
    def _observe(self) -> str:
        files = sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("*.py")
            if ".git" not in p.parts and "state" not in p.parts
        )
        recent = []
        for line in (self.chain.path.read_text().splitlines()[-5:] if self.chain.path.exists() else []):
            import json
            p = json.loads(line)["payload"]
            recent.append(f"{p['cycle_id']} [{p['approval_state']}] {p['proposal']}")
        return (
            f"REPO FILES ({len(files)}):\n" + "\n".join(files) +
            "\n\nOBJECTIVES (weights):\n" + "\n".join(f"  {k}: {v}" for k, v in self.objectives.items()) +
            "\n\nRECENT CYCLES:\n" + ("\n".join(recent) or "(none)")
        )

    def _read_files(self, paths: list[str], budget: int = 30000) -> str:
        out, used = [], 0
        for rel in paths:
            fp = self.root / rel
            if fp.exists():
                txt = fp.read_text(encoding="utf-8", errors="replace")
                block = f"\n=== {rel} ===\n{txt}\n"
                if used + len(block) > budget:
                    break
                out.append(block); used += len(block)
        return "".join(out)

    def _git(self, *args: str, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(cwd or self.root), *args],
                              capture_output=True, text=True, timeout=timeout)

    def _promote(self, cycle_id: str, files: list[dict[str, str]], summary: str) -> dict[str, Any]:
        """Build the approved change on a fresh branch + push for PR. Never main."""
        branch = f"ecnyss/cycle-{cycle_id}"
        wt = Path(tempfile.mkdtemp(prefix="ecnyss_promote_"))
        try:
            add = self._git("worktree", "add", "-q", "-b", branch, str(wt), "HEAD")
            if add.returncode != 0:
                return {"promoted": False, "reason": f"worktree: {add.stderr.strip()[:160]}"}
            for f in files[:3]:
                target = wt / f["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f["content"], encoding="utf-8")
            self._git("add", "-A", cwd=wt)
            self._git("commit", "-q", "-m", f"ecnyss {cycle_id}: {summary}"[:100],
                      "--author=ecnyss <ecnyss@autonomous.local>", cwd=wt)
            push = self._git("push", "-q", "-u", "origin", branch, cwd=wt, timeout=90)
            pushed = push.returncode == 0
            pr_url = ""
            if pushed:
                pr = subprocess.run(
                    ["gh", "pr", "create", "--repo", "Cole-Will-I-Am/-cnesse",
                     "--head", branch, "--base", "main",
                     "--title", f"ecnyss {cycle_id}: {summary}"[:80],
                     "--body", "Autonomous Ecnyss change. Sandbox-tested, gate-approved. Human merge required."],
                    cwd=str(self.root), capture_output=True, text=True, timeout=60,
                )
                pr_url = pr.stdout.strip() if pr.returncode == 0 else f"(pr_failed: {pr.stderr.strip()[:120]})"
            return {"promoted": pushed, "branch": branch, "pr_url": pr_url}
        finally:
            self._git("worktree", "remove", "--force", str(wt))

    # ---- cycles ------------------------------------------------------------
    def run_dry_cycle(self, proposal: str, why: str) -> dict[str, Any]:
        basis_ref = self.chain.head()
        prov = Provenance(why=why, objective_refs=["correctness"],
                          evidence=[Evidence("dry_run", basis_ref, "record-only", 1.0)])
        art = CycleArtifact(proposal=proposal, basis_ref=basis_ref, provenance=prov, approval_state="pending")
        block = emit(self.chain, art)
        ok, detail = self.chain.verify()
        return {"cycle_id": art.cycle_id, "block_index": block["index"], "chain_ok": ok, "chain_detail": detail}

    def evolve(self) -> dict[str, Any]:
        cycle_id = uuid.uuid4().hex[:12]
        basis_ref = self.chain.head()
        rollback_ref = self._git("rev-parse", "HEAD").stdout.strip()
        observation = self._observe()

        goal = self.agents["architect"].run(
            f"Choose this cycle's single highest-leverage goal.\n\n{observation}")
        plan = self.agents["planner"].run(
            f"GOAL:\n{goal}\n\n{observation}\n\nProduce a minimal one-cycle change spec (<=3 files + which tests verify it).")
        # Coder gets the plan plus current content of any files it likely needs.
        import re
        hinted = [f for f in re.findall(r"[\w/]+\.py", plan)][:3]
        coder_out = self.agents["coder"].run(
            f"PLAN:\n{plan}\n\nCURRENT FILES:\n{self._read_files(hinted)}\n\n"
            "Return ONLY the strict JSON change object.")
        change = extract_json(coder_out)

        result: dict[str, Any] = {"cycle_id": cycle_id, "goal": goal[:200]}
        if not change or "files" not in change or not change.get("files"):
            return self._record(cycle_id, basis_ref, rollback_ref, goal, "rejected",
                                 why="coder produced no valid change",
                                 evidence=[Evidence("coder", basis_ref, "invalid/empty JSON", 0.2)],
                                 result=result, extra={"rejected": "no_valid_change"})

        action = str(change.get("action", "modify"))
        files = [f for f in change["files"] if isinstance(f, dict) and f.get("path") and f.get("content")]

        # Sandbox: verify before promote.
        report = self.sandbox.evaluate(files, action)
        tests_passed = bool(report.get("tests", {}).get("passed"))

        # Red team.
        rt = self.agents["redteam"].run(
            f"PROPOSED CHANGE: {change.get('summary','')}\nACTION: {action}\nFILES: {[f['path'] for f in files]}\n"
            f"TEST RESULT: {report.get('tests', {}).get('detail','')}\n\nFind risks. End with verdict BLOCK or PASS.")
        redteam_blocked = "BLOCK" in rt.upper().split("PASS")[0][-400:] if "BLOCK" in rt.upper() else False

        # Score against objectives.
        scores = merge_gate.score_change(report, action, redteam_blocked, self.objectives)
        score = merge_gate.weighted(scores, self.objectives)

        # Maintainer (different model) decides.
        mnt = self.agents["maintainer"].run(
            f"Tests passed: {tests_passed}\nWeighted score: {score}\nRed team blocked: {redteam_blocked}\n"
            f"Summary: {change.get('summary','')}\n\nReturn JSON {{\"decision\":\"approve|reject\",\"reason\":\"...\"}}.")
        mnt_json = extract_json(mnt) or {}
        maintainer_approved = str(mnt_json.get("decision", "")).lower() == "approve"

        # Permission for the write scope.
        scope = "write_tests" if all("test" in f["path"] for f in files) else \
                ("write_docs" if all(f["path"].endswith(".md") for f in files) else "write_core_logic")
        perm = self.permissions.check(scope)
        permission_ok = perm in (Decision.ALLOW, Decision.GATED)

        approved, reason = merge_gate.decide(
            tests_passed=tests_passed, score=score, baseline=0.0, threshold=self.merge_threshold,
            redteam_blocked=redteam_blocked, maintainer_approved=maintainer_approved, permission_ok=permission_ok)

        promote = self._promote(cycle_id, files, change.get("summary", "evolution")) if approved else {"promoted": False}

        result.update({
            "action": action, "files": [f["path"] for f in files], "tests_passed": tests_passed,
            "score": score, "redteam_blocked": redteam_blocked, "maintainer_approved": maintainer_approved,
            "scope": scope, "permission": perm.value, "approved": approved, "reason": reason, "promote": promote,
        })
        evidence = [
            Evidence("test", report.get("diff_hash", basis_ref), report.get("tests", {}).get("detail", "")[:300],
                     1.0 if tests_passed else 0.0),
            Evidence("red_team", basis_ref, ("BLOCK" if redteam_blocked else "PASS") + ": " + rt[:200], 0.7),
            Evidence("score", basis_ref, f"weighted={score} {scores}", 0.8),
            Evidence("maintainer", basis_ref, mnt_json.get("reason", "")[:160], 0.7),
        ]
        return self._record(
            cycle_id, basis_ref, rollback_ref, change.get("summary", goal),
            "approved" if approved else "rejected",
            why=f"{reason} | goal: {goal[:120]}", evidence=evidence, result=result,
            diff_hash=report.get("diff_hash"), test_result_hash=report.get("tests", {}).get("report_hash"),
            score=scores)

    def _record(self, cycle_id, basis_ref, rollback_ref, proposal, approval_state, *,
                why, evidence, result, diff_hash=None, test_result_hash=None, score=None, extra=None):
        prov = Provenance(why=why, objective_refs=list(self.objectives.keys())[:1] or ["correctness"], evidence=evidence)
        art = CycleArtifact(
            proposal=str(proposal)[:300], basis_ref=basis_ref, provenance=prov, cycle_id=cycle_id,
            diff_hash=diff_hash, test_result_hash=test_result_hash, score=score or {},
            approval_state=approval_state, rollback_ref=rollback_ref)
        block = emit(self.chain, art)
        ok, detail = self.chain.verify()
        result.update({"approval_state": approval_state, "block_index": block["index"], "chain_ok": ok})
        if extra:
            result.update(extra)
        return result
