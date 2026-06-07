"""Pure-logic unit tests for ecnyss.util.predicates."""
import re
import unittest
from ecnyss.util.predicates import (
    all_of, any_of, none_of, complement,
    is_truthy, is_falsy, equals, matches,
    in_range, has_length, has_keys, is_instance,
)


class TestAllOf(unittest.TestCase):
    def test_all_true(self):
        p = all_of(lambda x: x > 0, lambda x: x < 10)
        self.assertTrue(p(5))
        self.assertFalse(p(-1))
        self.assertFalse(p(15))

    def test_empty_all_of_is_true(self):
        p = all_of()
        self.assertTrue(p("anything"))


class TestAnyOf(unittest.TestCase):
    def test_any_true(self):
        p = any_of(lambda x: x < 0, lambda x: x > 10)
        self.assertTrue(p(-5))
        self.assertTrue(p(15))
        self.assertFalse(p(5))

    def test_empty_any_of_is_false(self):
        p = any_of()
        self.assertFalse(p("anything"))


class TestNoneOf(unittest.TestCase):
    def test_none_true(self):
        p = none_of(lambda x: x < 0, lambda x: x > 10)
        self.assertTrue(p(5))
        self.assertFalse(p(-1))
        self.assertFalse(p(11))

    def test_empty_none_of_is_true(self):
        p = none_of()
        self.assertTrue(p("anything"))


class TestComplement(unittest.TestCase):
    def test_complement_flips(self):
        p = complement(lambda x: x > 0)
        self.assertTrue(p(-1))
        self.assertFalse(p(1))


class TestTruthiness(unittest.TestCase):
    def test_is_truthy(self):
        self.assertTrue(is_truthy(1))
        self.assertTrue(is_truthy("x"))
        self.assertTrue(is_truthy([1]))
        self.assertFalse(is_truthy(0))
        self.assertFalse(is_truthy(""))
        self.assertFalse(is_truthy([]))
        self.assertFalse(is_truthy(None))

    def test_is_falsy(self):
        self.assertTrue(is_falsy(0))
        self.assertTrue(is_falsy(""))
        self.assertTrue(is_falsy([]))
        self.assertTrue(is_falsy(None))
        self.assertFalse(is_falsy(1))
        self.assertFalse(is_falsy("x"))


class TestEquals(unittest.TestCase):
    def test_equals(self):
        p = equals(42)
        self.assertTrue(p(42))
        self.assertFalse(p(41))
        self.assertFalse(p("42"))


class TestMatches(unittest.TestCase):
    def test_matches_basic(self):
        p = matches(r"^\d{3}-\d{2}-\d{4}$")
        self.assertTrue(p("123-45-6789"))
        self.assertFalse(p("12-345-6789"))
        self.assertFalse(p("abc"))

    def test_matches_flags(self):
        p = matches(r"^hello$", re.IGNORECASE)
        self.assertTrue(p("HELLO"))
        self.assertTrue(p("hello"))
        self.assertFalse(p("world"))


class TestInRange(unittest.TestCase):
    def test_inclusive(self):
        p = in_range(0, 10)
        self.assertTrue(p(0))
        self.assertTrue(p(5))
        self.assertTrue(p(10))
        self.assertFalse(p(-1))
        self.assertFalse(p(11))

    def test_exclusive(self):
        p = in_range(0, 10, inclusive=False)
        self.assertFalse(p(0))
        self.assertTrue(p(5))
        self.assertFalse(p(10))


class TestHasLength(unittest.TestCase):
    def test_has_length(self):
        p = has_length(3)
        self.assertTrue(p([1, 2, 3]))
        self.assertTrue(p("abc"))
        self.assertTrue(p((1, 2, 3)))
        self.assertFalse(p([1, 2]))
        self.assertFalse(p("abcd"))


class TestHasKeys(unittest.TestCase):
    def test_has_keys(self):
        p = has_keys("a", "b")
        self.assertTrue(p({"a": 1, "b": 2, "c": 3}))
        self.assertTrue(p({"a": 1, "b": 2}))
        self.assertFalse(p({"a": 1}))
        self.assertFalse(p({}))


class TestIsInstance(unittest.TestCase):
    def test_is_instance_single(self):
        p = is_instance(int)
        self.assertTrue(p(1))
        self.assertFalse(p("1"))
        self.assertFalse(p(1.0))

    def test_is_instance_multiple(self):
        p = is_instance(int, float)
        self.assertTrue(p(1))
        self.assertTrue(p(1.0))
        self.assertFalse(p("1"))


if __name__ == "__main__":
    unittest.main()
