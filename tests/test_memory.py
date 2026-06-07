"""Tests for Phase 2 memory tiers and self/world model."""
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ecnyss.memory import MemoryEntry, SemanticIndex, Roadmap
from ecnyss.kernel.self_world import WorldModel

ROOT = Path(__file__).resolve().parents[1]


class TestMemoryEntry(unittest.TestCase):
    def test_grounded_trusted(self):
        e = MemoryEntry(key="k", value=1, source_ref="sha256:x", confidence=0.9)
        self.assertTrue(e.trusted())

    def test_stale_not_trusted(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        e = MemoryEntry(key="k", value=1, source_ref="x", confidence=0.9, revalidate_after=past)
        self.assertTrue(e.is_stale())
        self.assertFalse(e.trusted())

    def test_ungrounded_not_trusted(self):
        e = MemoryEntry(key="k", value=1, source_ref="", confidence=0.9)
        self.assertFalse(e.trusted())


class TestSemanticIndex(unittest.TestCase):
    def test_refresh_and_summary(self):
        idx = SemanticIndex(ROOT, "/tmp/ecnyss_test_semantic.json")
        stats = idx.refresh()
        self.assertGreater(stats["total"], 0)
        self.assertIn("CODEBASE MAP", idx.summary())
        # Second refresh: nothing changed -> all unchanged.
        stats2 = idx.refresh()
        self.assertEqual(stats2["updated"], 0)
        Path("/tmp/ecnyss_test_semantic.json").unlink(missing_ok=True)


class TestRoadmap(unittest.TestCase):
    def test_lesson_dedup_and_version(self):
        p = Path("/tmp/ecnyss_test_roadmap.json")
        p.unlink(missing_ok=True)
        rm = Roadmap(p)
        rm.add_lesson("do not break the chain", "cycle1")
        rm.add_lesson("do not break the chain", "cycle2")  # dup ignored
        self.assertIn("do not break the chain", rm.summary())
        p.unlink(missing_ok=True)


class TestWorldModel(unittest.TestCase):
    def test_mode(self):
        wm = WorldModel(ROOT / "config" / "world.yaml")
        self.assertIn(wm.mode, ("self", "target"))
        self.assertIn("WORLD-MODEL", wm.summary())


if __name__ == "__main__":
    unittest.main()
