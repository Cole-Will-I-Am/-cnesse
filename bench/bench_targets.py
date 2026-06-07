"""Aspirational capability targets — held-out, currently UNMET (so the benchmark
has headroom and a gradient). Each probe specifies a higher-order capability that
should be built by COMPOSING existing utils. As the lab builds them, the score
rises. The lab cannot see this file (bench/ is protected); the plain-language
targets are surfaced to it via the roadmap, not these assertions.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TaskPipeline(unittest.TestCase):
    """Target: ecnyss/compose/pipeline.py — run_pipeline(deps, fns) executes fns
    in dependency order (topological), passing accumulated results, returns dict."""
    def test_runs_in_dependency_order(self):
        from ecnyss.compose.pipeline import run_pipeline
        deps = {"a": set(), "b": set(), "c": {"a", "b"}}
        fns = {"a": lambda r: 1, "b": lambda r: 2, "c": lambda r: r["a"] + r["b"]}
        out = run_pipeline(deps, fns)
        self.assertEqual(out["c"], 3)


class Retry(unittest.TestCase):
    """Target: ecnyss/util/retry.py — retry(fn, attempts) -> Result (Ok/Err),
    composing util.results. Succeeds if fn returns within attempts."""
    def test_retry_succeeds_then_fails(self):
        from ecnyss.util.retry import retry
        calls = {"n": 0}
        def flaky(_=None):
            calls["n"] += 1
            if calls["n"] < 3:
                raise ValueError("not yet")
            return 42
        self.assertEqual(retry(flaky, attempts=3).unwrap_or(None), 42)
        self.assertIsNone(retry(lambda _=None: (_ for _ in ()).throw(RuntimeError), attempts=2).unwrap_or(None))


class SchemaValidate(unittest.TestCase):
    """Target: ecnyss/validate/schema.py — validate(data, spec) -> Result, where
    spec maps key->type; Ok(data) if all present & typed, else Err(list of issues)."""
    def test_valid_and_invalid(self):
        from ecnyss.validate.schema import validate
        spec = {"name": str, "age": int}
        self.assertTrue(validate({"name": "x", "age": 1}, spec).is_ok())
        self.assertTrue(validate({"name": "x"}, spec).is_err())


if __name__ == "__main__":
    unittest.main()
