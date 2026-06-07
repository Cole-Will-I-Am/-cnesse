"""Tests for the robust coder envelope parser and cooldown."""
import sys
import tempfile
import os
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ecnyss.cognition.agent import parse_file_blocks
from ecnyss.memory.cooldown import Cooldown


class TestParse(unittest.TestCase):
    def test_parses_multifile_with_tricky_content(self):
        text = ('ACTION: create\nSUMMARY: s\n'
                '@@FILE: a/b.py@@\nx = "a,b\\\\c"  # quotes + backslash\n@@ENDFILE@@\n'
                '@@FILE: tests/test_b.py@@\ndef test(): assert 1\n@@ENDFILE@@')
        c = parse_file_blocks(text)
        self.assertEqual([f["path"] for f in c["files"]], ["a/b.py", "tests/test_b.py"])
        self.assertIn("backslash", c["files"][0]["content"])

    def test_strips_thinking(self):
        text = "blah ...done thinking.\nACTION: create\nSUMMARY: s\n@@FILE: x.py@@\npass\n@@ENDFILE@@"
        self.assertIsNotNone(parse_file_blocks(text))

    def test_none_on_garbage(self):
        self.assertIsNone(parse_file_blocks("no blocks here"))


class TestCooldown(unittest.TestCase):
    def test_threshold_and_clear(self):
        c = Cooldown(os.path.join(tempfile.mkdtemp(), "cd.json"), threshold=3)
        for _ in range(3):
            c.record("t.py")
        self.assertIn("t.py", c.cooled())
        c.clear("t.py")
        self.assertEqual(c.cooled(), [])


if __name__ == "__main__":
    unittest.main()
