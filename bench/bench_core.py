"""Held-out capability benchmark — the lab never sees or edits this (bench/ is
protected and outside tests/ and ecnyss/). Probes assert CORRECT behaviour of
shipped modules; failures surface real bugs independently of the coder's own
tests. Run every cycle via `cli bench`; the score is the trajectory of "smarter".
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class Numbers(unittest.TestCase):
    def test_clamp(self):
        from ecnyss.util.numbers import clamp
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(99, 0, 10), 10)

    def test_sign(self):
        from ecnyss.util.numbers import sign
        self.assertEqual((sign(-3), sign(0), sign(2)), (-1, 0, 1))

    def test_is_close_infinity(self):
        from ecnyss.util.numbers import is_close
        self.assertTrue(is_close(0.1 + 0.2, 0.3))
        self.assertTrue(is_close(float("inf"), float("inf")))
        self.assertFalse(is_close(float("inf"), 1e300))
        self.assertFalse(is_close(1.0, 2.0))


class Graphs(unittest.TestCase):
    def test_has_cycle(self):
        from ecnyss.util.graphs import has_cycle
        self.assertTrue(has_cycle({1: {2}, 2: {1}}))
        self.assertFalse(has_cycle({1: {2}, 2: set()}))

    def test_topo_covers_all_nodes(self):
        from ecnyss.util.graphs import topological_sort
        self.assertEqual(len(topological_sort({1: {2}, 2: {3}, 3: set()})), 3)


class Dicts(unittest.TestCase):
    def test_deep_merge(self):
        from ecnyss.util.dicts import deep_merge
        self.assertEqual(deep_merge({"a": {"x": 1}}, {"a": {"y": 2}}), {"a": {"x": 1, "y": 2}})

    def test_pick_omit(self):
        from ecnyss.util.dicts import pick, omit
        self.assertEqual(pick({"a": 1, "b": 2}, ["a"]), {"a": 1})
        self.assertEqual(omit({"a": 1, "b": 2}, ["a"]), {"b": 2})


class Results(unittest.TestCase):
    def test_ok_err(self):
        from ecnyss.util.results import Ok, Err
        self.assertTrue(Ok(5).is_ok())
        self.assertEqual(Ok(5).unwrap_or(0), 5)
        self.assertEqual(Err("e").unwrap_or(0), 0)
        self.assertEqual(Ok(2).map(lambda x: x + 1).unwrap_or(0), 3)


class Functional(unittest.TestCase):
    def test_identity_and_pipe(self):
        from ecnyss.util.functional import identity, pipe, compose
        self.assertEqual(identity(5), 5)
        inc = lambda x: x + 1
        self.assertEqual(pipe(inc, inc)(0), 2)
        self.assertEqual(compose(inc, inc)(0), 2)


class Trees(unittest.TestCase):
    def test_get_set_in(self):
        from ecnyss.util.trees import get_in, set_in
        self.assertEqual(get_in({"a": {"b": 1}}, ["a", "b"]), 1)
        self.assertEqual(get_in({}, ["x"], default=9), 9)
        updated = set_in({"a": {}}, ["a", "b"], 5)
        self.assertEqual(get_in(updated, ["a", "b"]), 5)


if __name__ == "__main__":
    unittest.main()
