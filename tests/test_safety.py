"""Tests for Phase 3 containment: sandbox isolation + governance protection."""
import os
import shutil
import sys
import unittest
from pathlib import Path

# These tests spawn git worktrees + systemd-run, which the sandbox jail forbids.
# Skip them when running INSIDE the jail (the orchestrator sets ECNYSS_IN_JAIL),
# so a cycle's full-suite run isn't poisoned by the lab's own infra tests.
IN_JAIL = bool(os.environ.get("ECNYSS_IN_JAIL"))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
from ecnyss.kernel.sandbox import Sandbox

ROOT = Path(__file__).resolve().parents[1]


class TestSafetyConfig(unittest.TestCase):
    def test_protected_paths_declared(self):
        cfg = yaml.safe_load((ROOT / "config" / "safety.yaml").read_text())
        prot = set(cfg["protected_paths"])
        # The guardrails and enforcement code must be protected.
        for p in ["config/permissions.yaml", "ecnyss/kernel/permission_model.py",
                  "ecnyss/evolution/merge_gate.py", "ecnyss/protocol/hash_chain.py"]:
            self.assertIn(p, prot)


@unittest.skipIf(IN_JAIL, "process-spawning sandbox tests cannot run inside the jail")
class TestSandboxIsolation(unittest.TestCase):
    def test_test_cmd_is_jailed_when_available(self):
        sb = Sandbox(ROOT)
        cmd, mode = sb._test_cmd(Path("/tmp"))
        if shutil.which("systemd-run"):
            self.assertIn("systemd-run", cmd)
            self.assertIn("--property=PrivateNetwork=yes", cmd)
            self.assertTrue(any(c.startswith("--uid=") for c in cmd))
            self.assertIn("jail", mode)
        else:
            self.assertIn("unisolated", mode)

    def test_unsafe_paths_rejected(self):
        sb = Sandbox(ROOT)
        for bad in [{"path": "../escape.py", "content": "x"},
                    {"path": ".github/workflows/ci.yml", "content": "x"},
                    {"path": "config/secret_keys.py", "content": "x"}]:
            rep = sb.evaluate([bad], "create")
            self.assertIn("error", rep, f"should reject {bad['path']}")


if __name__ == "__main__":
    unittest.main()
