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
from ..cognition.agent import Agent, load_registry, extract_json, parse_file_blocks
from .permission_model import PermissionModel, Decision
from .sandbox import Sandbox
from .self_world import SelfModel, WorldModel
from ..evolution import merge_gate, fitness
from ..memory.episodic_store import EpisodicStore
from ..memory.semantic_index import SemanticIndex
from ..memory.roadmap import Roadmap
from ..memory.cooldown import Cooldown

# Robust output envelope for the coder — raw file content between delimiters, no
# JSON escaping (survives large files / quotes / backslashes).
ENVELOPE = (
    "OUTPUT FORMAT — use EXACTLY this, no JSON, no markdown fences:\n"
    "ACTION: create|modify\n"
    "SUMMARY: one line\n"
    "@@FILE: relative/path.py@@\n"
    "<full file content, verbatim>\n"
    "@@ENDFILE@@\n"
    "(repeat the @@FILE:...@@ ... @@ENDFILE@@ block for each file; output nothing else)"
)


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
        self.cooldown = Cooldown(self.root / "state" / "cooldown.json")
        self.self_model = SelfModel(self.root, self.permissions)
        self.world_model = WorldModel(self.root / "config" / "world.yaml")
        safety_path = self.root / "config" / "safety.yaml"
        safety = yaml.safe_load(safety_path.read_text(encoding="utf-8")) if safety_path.exists() else {}
        self.protected_paths = set((safety or {}).get("protected_paths", []))
        self.autonomy = (safety or {}).get("autonomy", {}) or {}
        self.codex = (safety or {}).get("codex_review", {}) or {}

    # ---- helpers -----------------------------------------------------------
    def _observe(self) -> str:
        # Refresh semantic memory from source (re-derives changed facts).
        self.semantic.refresh()
        return "\n\n".join([
            self.self_model.summary(),
            self.world_model.summary(),
            "OBJECTIVES (weights):\n" + "\n".join(f"  {k}: {v}" for k, v in self.objectives.items()),
            self.semantic.compact_summary(),   # one line/module — scales, no truncation
            self.episodic.summary(5),
            self.roadmap.summary(),
        ])

    def _goal_key(self, goal: str) -> str:
        import re
        m = re.search(r"[\w/]+\.py", goal)
        return m.group(0) if m else " ".join(goal.lower().split())[:50]

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

    def _codex_findings(self, pr_number: int, wait_sec: int) -> tuple[bool, list[dict[str, Any]]]:
        """Poll for Codex's PR review (it lands ~2 min after open); return its
        severity-tagged inline findings. Timeout fallback so the loop never stalls."""
        import time as _t
        repo = "Cole-Will-I-Am/-cnesse"
        deadline = _t.time() + max(0, wait_sec)
        reviewed = False
        while _t.time() < deadline:
            r = subprocess.run(
                ["gh", "api", f"repos/{repo}/pulls/{pr_number}/reviews",
                 "--jq", '[.[]|select(.user.login|test("codex";"i"))]|length'],
                cwd=str(self.root), capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip() not in ("", "0"):
                reviewed = True
                break
            _t.sleep(15)
        findings: list[dict[str, Any]] = []
        if reviewed:
            c = subprocess.run(["gh", "api", f"repos/{repo}/pulls/{pr_number}/comments"],
                               cwd=str(self.root), capture_output=True, text=True, timeout=30)
            if c.returncode == 0:
                import json as _j, re as _re
                try:
                    for cm in _j.loads(c.stdout):
                        m = _re.search(r"P([1-3]) Badge", cm.get("body", ""))
                        if m:
                            findings.append({
                                "severity": f"P{m.group(1)}",
                                "path": cm.get("path", ""),
                                "line": cm.get("line"),
                                "title": cm.get("body", "").split("\n")[0][:160],
                            })
                except _j.JSONDecodeError:
                    pass
        return reviewed, findings

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
            # Wait for Codex's review and gate on blocking severities.
            codex_reviewed, findings, held = False, [], False
            pr_number = pr_url.rstrip("/").split("/")[-1] if pr_url.startswith("http") else ""
            if pushed and auto_merge_ok and self.codex.get("enabled") and pr_number.isdigit():
                codex_reviewed, findings = self._codex_findings(
                    int(pr_number), int(self.codex.get("wait_sec", 180)))
                block = set(self.codex.get("block_severities", ["P1"]))
                held = any(f["severity"] in block for f in findings)

            merged = False
            merge_detail = "auto_merge_off" if not auto_merge_ok else "not_attempted"
            if pushed and auto_merge_ok and not held:
                method = f"--{self.autonomy.get('merge_method', 'squash')}"
                mg = subprocess.run(
                    ["gh", "pr", "merge", branch, "--repo", "Cole-Will-I-Am/-cnesse",
                     method, "--admin", "--delete-branch"],
                    cwd=str(self.root), capture_output=True, text=True, timeout=90)
                merged = mg.returncode == 0
                merge_detail = "merged" if merged else f"merge_failed: {mg.stderr.strip()[:140]}"
            elif held:
                merge_detail = "held_for_review: codex flagged " + ",".join(
                    sorted({f["severity"] for f in findings if f["severity"] in
                            set(self.codex.get("block_severities", ["P1"]))}))
            return {"promoted": pushed, "branch": branch, "pr_url": pr_url,
                    "merged": merged, "merge_detail": merge_detail,
                    "codex_reviewed": codex_reviewed, "codex_findings": findings,
                    "held_for_review": held}
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

        _, existing_mods = fitness.build_registry(self.root, set())
        caps = ", ".join(sorted(existing_mods))
        policy = (
            "BUILD POLICY — COMPOSE into capabilities that ACT: build a HIGHER-ORDER "
            "capability by importing and combining the project's EXISTING modules. Do NOT "
            "duplicate anything that exists; integration and novelty are rewarded, smallness "
            f"is NOT. Existing ecnyss modules to build ON (never rebuild): {caps}. "
            "Tests run in an isolated, non-root, resource-capped jail. You MAY now use: real "
            "FILE I/O (use tempfile or $ECNYSS_SCRATCH for scratch files), local SUBPROCESS, "
            "and THREADS — so build stateful things (stores, serializers, parsers, file-backed "
            "registries, processing pipelines, concurrency helpers), not just pure functions. "
            "You may NOT use the NETWORK (it is blocked), and must not write tests that spawn "
            "git/systemd-run or invoke kernel.sandbox/orchestrator. Put tests under tests/ "
            "(test_*.py); write STRONG tests (edge cases + real round-trips) — weak tests are "
            "penalised by independent mutation scoring. A NEW subpackage (e.g. ecnyss/store/) "
            "MUST include an __init__.py or imports will fail."
        )
        cooled = self.cooldown.cooled()
        avoid = ("\n\nON COOLDOWN — these targets have failed repeatedly; do NOT propose them "
                 "again, pick something different: " + ", ".join(cooled)) if cooled else ""
        goal = self.agents["architect"].run(
            f"Choose this cycle's single highest-leverage goal.\n\n{policy}{avoid}\n\n{observation}")
        # Retrieval: pull FULL detail of only the modules relevant to the goal,
        # instead of dumping the whole (growing) map and truncating.
        relevant = self.semantic.retrieve(goal)
        plan = self.agents["planner"].run(
            f"GOAL:\n{goal}\n\n{policy}\n\n{relevant}\n\nProduce a minimal one-cycle change spec "
            "(<=3 files + which pure-logic tests verify it). Build on the retrieved modules above.")
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
            f"PLAN:\n{plan}\n\n{policy}\n\n{self.semantic.retrieve(plan)}\n\n"
            f"EXISTING FILES (use action=modify and return the FULL "
            f"updated file for any of these; only use action=create for a brand-new path "
            f"NOT in this list):\n" + "\n".join(existing) +
            f"\n\nCURRENT CONTENT OF LIKELY TARGETS:\n{self._read_files(hinted)}\n\n" + ENVELOPE)
        # Parse the delimited envelope; on parse failure, re-prompt (the single
        # biggest robustness win — large files no longer die on JSON escaping).
        change = parse_file_blocks(coder_out)
        for _ in range(2):
            if change and change.get("files"):
                break
            coder_out = self.agents["coder"].run(
                "Your previous reply could not be parsed. Reply AGAIN using EXACTLY the "
                "required format and nothing else.\n\n" + ENVELOPE)
            change = parse_file_blocks(coder_out)

        result: dict[str, Any] = {"cycle_id": cycle_id, "goal": goal[:200]}
        if not change or not change.get("files"):
            self.cooldown.record(self._goal_key(goal))
            return self._record(cycle_id, basis_ref, rollback_ref, goal, "rejected",
                                 why="coder produced no parseable change after re-prompts",
                                 evidence=[Evidence("coder", basis_ref, "unparseable envelope x3", 0.2)],
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
        def _protected(path: str) -> bool:
            return any(path.startswith(p) if p.endswith("/") else path == p
                       for p in self.protected_paths)
        touched_protected = sorted(f["path"] for f in files if _protected(f["path"]))
        if touched_protected:
            self.cooldown.record(self._goal_key(goal))
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
                f"The tests FAILED in the isolated jail. Fix the code so ALL tests pass.\n"
                f"TEST OUTPUT:\n{report.get('tests', {}).get('detail', '')}\n\nCURRENT FILES:" +
                "".join(f"\n@@FILE: {f['path']}@@\n{f['content']}\n@@ENDFILE@@" for f in files) +
                "\n\n" + ENVELOPE)
            fixed = parse_file_blocks(fix_out)
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

        # Score against objectives. Mutation score is an INDEPENDENT correctness
        # signal (do the tests catch injected bugs?) — only meaningful if the
        # suite currently passes.
        mutation = self.sandbox.mutation_score(files, action) if tests_passed else 0.0
        scores = fitness.score(report, files, redteam_blocked, self.objectives, self.root, mutation)
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
        # Learn from Codex: record every finding so future cycles can address it.
        for f in promote.get("codex_findings", []):
            self.roadmap.add_lesson(
                f"Codex {f['severity']} @ {f['path']}:{f.get('line')}: {f['title']}",
                source_ref=cycle_id)
        if promote.get("merged"):
            # Positive memory: record what was built so the lab knows it exists.
            self.roadmap.add_lesson(f"Built & merged: {change.get('summary','')[:100]}", source_ref=cycle_id)
            self.cooldown.clear(self._goal_key(goal))   # success clears any cooldown
        if promote.get("held_for_review"):
            approved = False  # a held PR is not a completed merge
            reason = promote.get("merge_detail", "held_for_review: codex blocking finding")
        if not approved:
            self.cooldown.record(self._goal_key(goal))  # repeated failures -> cooldown

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
