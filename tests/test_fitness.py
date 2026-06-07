"""Tests for the capability-oriented fitness function."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ecnyss.evolution import fitness

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {"correctness": 0.2, "test_strength": 0.2, "integration": 0.2,
           "capability_gain": 0.2, "maintainability": 0.1, "security": 0.1}


def _rep(passed=True):
    return {"tests": {"passed": passed, "detail": "Ran 5 tests\nOK"}}


class TestFitness(unittest.TestCase):
    def test_failing_tests_zero_correctness(self):
        s = fitness.score(_rep(False), [], False, WEIGHTS, ROOT)
        self.assertEqual(s["correctness"], 0.0)

    def test_mutation_passthrough(self):
        s = fitness.score(_rep(), [], False, WEIGHTS, ROOT, mutation_score=0.9)
        self.assertEqual(s["test_strength"], 0.9)

    def test_integration_rewards_own_imports(self):
        f = [{"path": "ecnyss/_x.py", "content": "from ecnyss.util.numbers import clamp\nfrom ecnyss.util.stats import mean\ndef f():\n    return clamp(mean([1,2]),0,1)\n"}]
        s = fitness.score(_rep(), f, False, WEIGHTS, ROOT)
        self.assertGreaterEqual(s["integration"], 0.9)

    def test_isolated_leaf_scores_low_integration(self):
        f = [{"path": "ecnyss/_y.py", "content": "def standalone():\n    return 1\n"}]
        s = fitness.score(_rep(), f, False, WEIGHTS, ROOT)
        self.assertLessEqual(s["integration"], 0.3)

    def test_duplicate_module_penalised(self):
        # rebuilding an existing module wholesale with no novel symbols -> low cap.
        existing_syms, _ = fitness.build_registry(ROOT, set())
        dup = next(iter(existing_syms))
        f = [{"path": "ecnyss/util/intervals.py", "content": f"def {dup}():\n    return 1\n"}]
        s = fitness.score(_rep(), f, False, WEIGHTS, ROOT)
        self.assertLessEqual(s["capability_gain"], 0.2)

    def test_redteam_block_zeroes_security(self):
        s = fitness.score(_rep(), [], True, WEIGHTS, ROOT)
        self.assertEqual(s["security"], 0.0)

    def test_registry_nonempty(self):
        syms, mods = fitness.build_registry(ROOT, set())
        self.assertTrue(syms and mods)


if __name__ == "__main__":
    unittest.main()
