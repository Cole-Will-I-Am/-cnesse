"""Pure-logic unit tests for ecnyss.util.numbers."""

import math
import unittest
from ecnyss.util.numbers import (
    clamp, sign, lerp, normalize, remap, round_to, is_close,
)

class TestClamp(unittest.TestCase):
    def test_within_bounds(self):
        self.assertEqual(clamp(5, 0, 10), 5)
    def test_below_min(self):
        self.assertEqual(clamp(-3, 0, 10), 0)
    def test_above_max(self):
        self.assertEqual(clamp(15, 0, 10), 10)
    def test_exact_bounds(self):
        self.assertEqual(clamp(0, 0, 10), 0)
        self.assertEqual(clamp(10, 0, 10), 10)
    def test_invalid_bounds_raises(self):
        with self.assertRaises(ValueError):
            clamp(5, 10, 0)

class TestSign(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(sign(3.14), 1)
    def test_negative(self):
        self.assertEqual(sign(-2.5), -1)
    def test_zero(self):
        self.assertEqual(sign(0), 0)
        self.assertEqual(sign(-0.0), 0)

class TestLerp(unittest.TestCase):
    def test_endpoints(self):
        self.assertEqual(lerp(0, 10, 0), 0)
        self.assertEqual(lerp(0, 10, 1), 10)
    def test_midpoint(self):
        self.assertEqual(lerp(0, 10, 0.5), 5)
    def test_extrapolation(self):
        self.assertEqual(lerp(0, 10, -1), -10)
        self.assertEqual(lerp(0, 10, 2), 20)

class TestNormalize(unittest.TestCase):
    def test_endpoints(self):
        self.assertEqual(normalize(0, 0, 10), 0.0)
        self.assertEqual(normalize(10, 0, 10), 1.0)
    def test_midpoint(self):
        self.assertEqual(normalize(5, 0, 10), 0.5)
    def test_out_of_range(self):
        self.assertEqual(normalize(-5, 0, 10), -0.5)
        self.assertEqual(normalize(15, 0, 10), 1.5)
    def test_invalid_range_raises(self):
        with self.assertRaises(ValueError):
            normalize(5, 10, 10)

class TestRemap(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(remap(5, 0, 10, 0, 10), 5)
    def test_scale(self):
        self.assertEqual(remap(5, 0, 10, 0, 100), 50)
    def test_shift_and_scale(self):
        self.assertEqual(remap(0, -10, 10, 0, 1), 0.5)

class TestRoundTo(unittest.TestCase):
    def test_integer_precision(self):
        self.assertEqual(round_to(3.14159, 0), 3.0)
    def test_decimal_precision(self):
        self.assertEqual(round_to(3.14159, 2), 3.14)
        self.assertEqual(round_to(3.14659, 2), 3.15)
    def test_negative_values(self):
        self.assertEqual(round_to(-3.14159, 2), -3.14)
        self.assertEqual(round_to(-3.14659, 2), -3.15)
    def test_negative_precision_raises(self):
        with self.assertRaises(ValueError):
            round_to(1.23, -1)

class TestIsClose(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(is_close(1.0, 1.0))
    def test_rel_tol(self):
        self.assertTrue(is_close(1.0, 1.000000001, rel_tol=1e-8))
        self.assertFalse(is_close(1.0, 1.0001, rel_tol=1e-8))
    def test_abs_tol(self):
        self.assertTrue(is_close(1e-12, 0.0, abs_tol=1e-10))
        self.assertFalse(is_close(1e-8, 0.0, abs_tol=1e-10))
    def test_zero_handling(self):
        self.assertTrue(is_close(0.0, 0.0))
        self.assertTrue(is_close(1e-15, 0.0, abs_tol=1e-10))
    def test_nan_inf(self):
        self.assertFalse(is_close(float('nan'), float('nan')))
        self.assertFalse(is_close(float('inf'), float('inf')))
        self.assertFalse(is_close(float('inf'), 1e300))

if __name__ == "__main__":
    unittest.main()
