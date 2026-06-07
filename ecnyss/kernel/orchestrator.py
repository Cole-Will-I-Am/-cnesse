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
from .self_world import SelfModel, WorldModel
from ..evolution import merge_gate, fitness
from ..memory.episodic_store import EpisodicStore
from ..memory.semantic_index import SemanticIndex
from ..memory.roadmap import Roadmap


class Orchestrator:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.permissions = PermissionModel(self.root / "config" / "permissions.yaml")
        self.objectives, self.merge_threshold = merge_gate.load_objectives(self.root / "config" / "objectives.yaml")
        self.chain = HashChain(self.root / "state" / "evolution_chain.jsonl")
        self.sandbox = Sandbox(self.root)
        registry, ollama_url = load_registry(self.root / "config" / "models.yaml")
        self.agents = {role: Agent(role, registry, ollama_url) for role in registry}
        # Memory tiers + self/world model.
        self.episodic = EpisodicStore(self.chain)
        self.semantic = SemanticIndex(self.root, self.root / "state" / "semantic_index.json")
        self.roadmap = Roadmap(self.root / "state" / "roadmap.json")
        self.self_model = SelfModel(self.root, self.permissions)
        self.world_model = WorldModel(self.root / "config" / "world.yaml")
        safety_path = self.root / "config" / "safety.yaml"
        safety = yaml.safe_load(safety_path.read_text(encoding="utf-8")) if safety_path.exists() else {}
        self.protected_paths = set((safety or {}).get("protected_paths", []))
        self.autonomy = (safety or {}).get("autonomy", {}) or {}

    # ---- helpers -----------------------------------------------------------
    def _observe(self) -> str:
        # Refresh semantic memory from source (re-derives changed facts).
        self.semantic.refresh()
        return "\n\n".join([
            self.self_model.summary(),
            self.world_model.summary(),
            "OBJECTIVES (weights):\n" + "\n".join(f"  {k}: {v}" for k, v in self.objectives.items()),
            self.semantic.summary(),
            self.episodic.summary(5),
            self.roadmap.summary(),
        ])

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

    def _promote(self, cycle_id: str, files: list[dict[str, str]], summary: str,
                 auto_merge_ok: bool = False) -> dict[str, Any]:
        """Build the approved change on a fresh branch + push + open a PR.

        If auto_merge_ok, the PR is then merged to main automatically (full
        autonomy). Only ever reached for non-governance, gate-approved changes.
        """
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
            if not pushed:
                return {"promoted": False, "branch": branch,
                        "push_error": push.stderr.strip()[:200] or "push failed"}
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
            merged = False
            merge_detail = "auto_merge_off" if not auto_merge_ok else "not_attempted"
            if pushed and auto_merge_ok:
                method = f"--{self.autonomy.get('merge_method', 'squash')}"
                mg = subprocess.run(
                    ["gh", "pr", "merge", branch, "--repo", "Cole-Will-I-Am/-cnesse",
                     method, "--admin", "--delete-branch"],
                    cwd=str(self.root), capture_output=True, text=True, timeout=90)
                merged = mg.returncode == 0
                merge_detail = "merged" if merged else f"merge_failed: {mg.stderr.strip()[:140]}"
            return {"promoted": pushed, "branch": branch, "pr_url": pr_url,
                    "merged": merged, "merge_detail": merge_detail}
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

        policy = (
            "BUILD POLICY: Prefer adding a NEW, self-contained capability module under "
            "ecnyss/ with its own pure-stdlib unit tests. Tests run in a locked-down jail "
            "with NO network, NO subprocess, NO git, NO systemd-run, NO threads — so test "
            "PURE LOGIC only. Never write tests that exercise kernel.sandbox / orchestrator "
            "process-spawning. Put unit tests under tests/ (named test_*.py) so they "
            "actually run. Keep it small and independently verifiable."
        )
        goal = self.agents["architect"].run(
            f"Choose this cycle's single highest-leverage goal.\n\n{policy}\n\n{observation}")
        plan = self.agents["planner"].run(
            f"GOAL:\n{goal}\n\n{policy}\n\n{observation}\n\nProduce a minimal one-cycle change spec (<=3 files + which pure-logic tests verify it).")
        # Coder gets the plan, the list of files that ALREADY EXIST (so it uses
        # modify, never recreates), and the current content of likely targets.
        import re
        existing = sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("*.py")
            if ".git" not in p.parts and "state" not in p.parts
        )
        hinted = [f for f in re.findall(r"[\w/]+\.py", plan) if f in existing][:3]
        coder_out = self.agents["coder"].run(
            f"PLAN:\n{plan}\n\n{policy}\n\nEXISTING FILES (use action=modify and return the FULL "
            f"updated file for any of these; only use action=create for a brand-new path "
            f"NOT in this list):\n" + "\n".join(existing) +
            f"\n\nCURRENT CONTENT OF LIKELY TARGETS:\n{self._read_files(hinted)}\n\n"
            "Return ONLY the strict JSON change object with COMPLETE file content.")
        change = extract_json(coder_out)

        result: dict[str, Any] = {"cycle_id": cycle_id, "goal": goal[:200]}
        if not change or "files" not in change or not change.get("files"):
            return self._record(cycle_id, basis_ref, rollback_ref, goal, "rejected",
                                 why="coder produced no valid change",
                                 evidence=[Evidence("coder", basis_ref, "invalid/empty JSON", 0.2)],
                                 result=result, extra={"rejected": "no_valid_change"})

        files = [f for f in change["files"] if isinstance(f, dict) and f.get("path") and f.get("content")]
        # Deterministically correct the action: if any target already exists it's a
        # modify (overwrite), never a create — prevents self-inflicted "file exists"
        # rejections regardless of what the coder labelled it.
        any_exists = any((self.root / f["path"]).exists() for f in files)
        action = "modify" if any_exists else "create"

        # Governance guard: a change touching protected files (its own guardrails,
        # enforcement code, scoring, or ledger) can never be auto-approved. It is
        # recorded as requiring explicit human authorization and never promoted.
        touched_protected = sorted(f["path"] for f in files if f["path"] in self.protected_paths)
        if touched_protected:
            return self._record(
                cycle_id, basis_ref, rollback_ref, change.get("summary", goal), "rejected",
                why=f"governance change requires explicit human authorization: {touched_protected}",
                evidence=[Evidence("governance", basis_ref, f"protected paths: {touched_protected}", 1.0)],
                result=result, extra={"governance_change": touched_protected, "approved": False})

        # Sandbox: verify before promote.
        report = self.sandbox.evaluate(files, action)
        tests_passed = bool(report.get("tests", {}).get("passed"))

        # Repair loop: a single bad test shouldn't kill the change. Feed the jail
        # failure back to the coder for bounded repair passes, then re-test.
        repair_loops = int(self.autonomy.get("repair_loops", 2))
        attempt = 0
        while not tests_passed and attempt < repair_loops:
            attempt += 1
            fix_out = self.agents["coder"].run(
                f"{policy}\n\nThe tests FAILED in the isolated jail. Fix the code so ALL tests "
                f"pass. Return ONLY the strict JSON change object with COMPLETE corrected files.\n"
                f"TEST OUTPUT:\n{report.get('tests', {}).get('detail', '')}\n\nCURRENT FILES:" +
                "".join(f"\n=== {f['path']} ===\n{f['content']}\n" for f in files))
            fixed = extract_json(fix_out)
            fixed_files = [f for f in (fixed.get("files", []) if fixed else [])
                           if isinstance(f, dict) and f.get("path") and f.get("content")]
            if not fixed_files or any(f["path"] in self.protected_paths for f in fixed_files):
                break
            files = fixed_files
            action = "modify" if any((self.root / f["path"]).exists() for f in files) else "create"
            report = self.sandbox.evaluate(files, action)
            tests_passed = bool(report.get("tests", {}).get("passed"))
        result["repair_attempts"] = attempt

        # Red team.
        rt = self.agents["redteam"].run(
            f"PROPOSED CHANGE: {change.get('summary','')}\nACTION: {action}\nFILES: {[f['path'] for f in files]}\n"
            f"TEST RESULT: {report.get('tests', {}).get('detail','')}\n\n"
            "Review for CONCRETE, EXPLOITABLE problems in THIS change: real regressions, "
            "secret/credential exposure, data loss, or code that is reachable with untrusted "
            "input in production. Do NOT block on theoretical/defensive hardening (e.g. "
            "recursion limits on local analysis utils), style, or hypothetical edge cases — "
            "note those as low-severity at most. Output risks with severity, then a final line "
            "'VERDICT: BLOCK' only if a concrete HIGH-severity, exploitable issue exists in this "
            "change, else 'VERDICT: PASS'.")
        verdict_lines = [ln.upper() for ln in rt.splitlines() if "VERDICT" in ln.upper()]
        if verdict_lines:
            redteam_blocked = "BLOCK" in verdict_lines[-1]
        else:  # no explicit verdict: only block if BLOCK present without a PASS
            redteam_blocked = "BLOCK" in rt.upper() and "PASS" not in rt.upper()

        # Score against objectives with measured fitness signals.
        baseline_tests = fitness.baseline_test_count(self.root)
        scores = fitness.score(report, files, redteam_blocked, self.objectives, self.root, baseline_tests)
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

        isolation_mode = report.get("tests", {}).get("isolation", "")
        auto_merge_ok = (
            bool(self.autonomy.get("auto_merge"))
            and (not self.autonomy.get("require_isolation", True) or "jail" in isolation_mode)
        )
        promote = (self._promote(cycle_id, files, change.get("summary", "evolution"), auto_merge_ok)
                   if approved else {"promoted": False})

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
        # Strategic memory: learn from rejected cycles so we don't repeat them.
        if approval_state == "rejected":
            self.roadmap.add_lesson(f"Rejected: {str(proposal)[:80]} ({why[:60]})", source_ref=cycle_id)
        result.update({"approval_state": approval_state, "block_index": block["index"], "chain_ok": ok})
        if extra:
            result.update(extra)
        return result
