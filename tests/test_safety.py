"""Tests for Phase 3 containment: sandbox isolation + governance protection."""
import shutil
import sys
import unittest
from pathlib import Path

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
