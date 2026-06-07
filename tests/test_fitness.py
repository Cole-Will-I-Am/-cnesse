"""Tests for the measured fitness function."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ecnyss.evolution import fitness

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {"correctness": 0.35, "test_coverage": 0.2, "maintainability": 0.15,
           "simplicity": 0.1, "capability_gain": 0.1, "security": 0.1}


class TestFitness(unittest.TestCase):
    def test_failing_tests_zero_correctness(self):
        rep = {"tests": {"passed": False, "detail": "Ran 3 tests\nFAILED"}}
        s = fitness.score(rep, [], False, WEIGHTS, ROOT, 5)
        self.assertEqual(s["correctness"], 0.0)

    def test_added_passing_tests_reward_coverage(self):
        rep = {"tests": {"passed": True, "detail": "Ran 10 tests\nOK"}}
        s = fitness.score(rep, [], False, WEIGHTS, ROOT, baseline_tests=5)
        self.assertEqual(s["correctness"], 1.0)
        self.assertGreaterEqual(s["test_coverage"], 0.9)

    def test_redteam_block_zeroes_security(self):
        rep = {"tests": {"passed": True, "detail": "Ran 5 tests\nOK"}}
        s = fitness.score(rep, [], True, WEIGHTS, ROOT, 5)
        self.assertEqual(s["security"], 0.0)

    def test_capability_gain_counts_new_public_symbols(self):
        files = [{"path": "ecnyss/_tmp_new.py", "content": "def alpha():\n    return 1\nclass Beta:\n    pass\n"}]
        s = fitness.score({"tests": {"passed": True, "detail": "Ran 1 test"}}, files, False, WEIGHTS, ROOT, 0)
        self.assertGreater(s["capability_gain"], 0.5)

    def test_baseline_counts_existing_tests(self):
        self.assertGreater(fitness.baseline_test_count(ROOT), 0)


if __name__ == "__main__":
    unittest.main()
