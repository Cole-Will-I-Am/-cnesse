"""Tests for the audit spine: canonical hashing, chain integrity, provenance, permissions."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ecnyss.protocol import HashChain, Provenance, Evidence, CycleArtifact, emit
from ecnyss.protocol.canonical import sha256_hex
from ecnyss.kernel import PermissionModel, Decision


class TestCanonical(unittest.TestCase):
    def test_order_independent(self):
        self.assertEqual(sha256_hex({"a": 1, "b": 2}), sha256_hex({"b": 2, "a": 1}))

    def test_value_sensitive(self):
        self.assertNotEqual(sha256_hex({"a": 1}), sha256_hex({"a": 2}))


class TestHashChain(unittest.TestCase):
    def setUp(self):
        self.path = Path("/tmp/ecnyss_test_chain.jsonl")
        self.path.unlink(missing_ok=True)
        self.chain = HashChain(self.path)

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_append_and_verify(self):
        self.chain.append({"x": 1})
        self.chain.append({"x": 2})
        ok, detail = self.chain.verify()
        self.assertTrue(ok, detail)
        self.assertEqual(self.chain.length(), 2)

    def test_tamper_detected(self):
        self.chain.append({"x": 1})
        self.chain.append({"x": 2})
        lines = self.path.read_text().splitlines()
        lines[0] = lines[0].replace('"x":1', '"x":99')
        self.path.write_text("\n".join(lines) + "\n")
        ok, _ = self.chain.verify()
        self.assertFalse(ok)


class TestProvenance(unittest.TestCase):
    def test_ungrounded_rejected(self):
        ok, _ = Provenance(why="", objective_refs=[], evidence=[]).is_grounded()
        self.assertFalse(ok)

    def test_grounded_ok(self):
        p = Provenance(why="fix bug", objective_refs=["correctness"],
                       evidence=[Evidence("test", "ref", "passes")])
        ok, _ = p.is_grounded()
        self.assertTrue(ok)

    def test_emit_requires_grounding(self):
        chain = HashChain("/tmp/ecnyss_test_emit.jsonl")
        Path("/tmp/ecnyss_test_emit.jsonl").unlink(missing_ok=True)
        bad = CycleArtifact(proposal="x", basis_ref="r", provenance=Provenance(why=""))
        with self.assertRaises(ValueError):
            emit(chain, bad)


class TestPermissions(unittest.TestCase):
    def setUp(self):
        self.pm = PermissionModel(Path(__file__).resolve().parents[1] / "config" / "permissions.yaml")

    def test_forbidden_pushes(self):
        self.assertIs(self.pm.check("push_to_main"), Decision.FORBIDDEN)

    def test_unknown_default_deny(self):
        self.assertIs(self.pm.check("nuke_everything"), Decision.FORBIDDEN)

    def test_docs_allowed(self):
        self.assertTrue(self.pm.autonomous_ok("write_docs"))


if __name__ == "__main__":
    unittest.main()
