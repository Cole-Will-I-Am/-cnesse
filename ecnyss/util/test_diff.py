"""Unit tests for ecnyss.util.diff module."""
from __future__ import annotations
import unittest
from ecnyss.util.diff import deep_equal, deep_diff


class TestDeepEqual(unittest.TestCase):
    """Tests for deep_equal function."""
    
    def test_primitives_equal(self):
        """Test primitive equality."""
        self.assertTrue(deep_equal(1, 1))
        self.assertTrue(deep_equal("hello", "hello"))
        self.assertTrue(deep_equal(3.14, 3.14))
        self.assertTrue(deep_equal(True, True))
        self.assertTrue(deep_equal(False, False))
        self.assertTrue(deep_equal(None, None))
    
    def test_primitives_unequal(self):
        """Test primitive inequality."""
        self.assertFalse(deep_equal(1, 2))
        self.assertFalse(deep_equal("hello", "world"))
        self.assertFalse(deep_equal(3.14, 2.71))
        self.assertFalse(deep_equal(True, False))
        self.assertFalse(deep_equal(None, 0))
    
    def test_empty_structures(self):
        """Test empty structures."""
        self.assertTrue(deep_equal({}, {}))
        self.assertTrue(deep_equal([], []))
        self.assertTrue(deep_equal((), ()))
        self.assertTrue(deep_equal(set(), set()))
    
    def test_nested_dicts(self):
        """Test nested dict equality."""
        a = {"x": {"y": {"z": 1}}}
        b = {"x": {"y": {"z": 1}}}
        c = {"x": {"y": {"z": 2}}}
        self.assertTrue(deep_equal(a, b))
        self.assertFalse(deep_equal(a, c))
    
    def test_nested_lists(self):
        """Test nested list equality."""
        a = [[1, 2], [3, 4]]
        b = [[1, 2], [3, 4]]
        c = [[1, 2], [3, 5]]
        self.assertTrue(deep_equal(a, b))
        self.assertFalse(deep_equal(a, c))
    
    def test_mixed_nested(self):
        """Test mixed nested structures."""
        a = {"list": [1, 2, {"key": "val"}], "tuple": (3, 4)}
        b = {"list": [1, 2, {"key": "val"}], "tuple": (3, 4)}
        c = {"list": [1, 2, {"key": "other"}], "tuple": (3, 4)}
        self.assertTrue(deep_equal(a, b))
        self.assertFalse(deep_equal(a, c))
    
    def test_sets(self):
        """Test set equality (unordered)."""
        a = {1, 2, 3}
        b = {3, 2, 1}
        c = {1, 2, 4}
        self.assertTrue(deep_equal(a, b))
        self.assertFalse(deep_equal(a, c))
    
    def test_list_tuple_equivalence(self):
        """Test list vs tuple with same content."""
        self.assertTrue(deep_equal([1, 2, 3], (1, 2, 3)))
        self.assertTrue(deep_equal((1, 2, 3), [1, 2, 3]))
        self.assertFalse(deep_equal([1, 2], (1, 2, 3)))
    
    def test_type_mismatch(self):
        """Test type mismatches."""
        self.assertFalse(deep_equal(1, "1"))
        self.assertFalse(deep_equal({}, []))
        self.assertFalse(deep_equal({"a": 1}, {"a": "1"}))


class TestDeepDiff(unittest.TestCase):
    """Tests for deep_diff function."""
    
    def test_identical_structures(self):
        """Test diff of identical structures."""
        a = {"x": 1, "y": 2}
        b = {"x": 1, "y": 2}
        diff = deep_diff(a, b)
        self.assertEqual(diff["added"], {})
        self.assertEqual(diff["removed"], {})
        self.assertEqual(diff["changed"], {})
        self.assertEqual(set(diff["unchanged"].keys()), {"x", "y"})
    
    def test_added_keys(self):
        """Test detection of added keys."""
        a = {"x": 1}
        b = {"x": 1, "y": 2}
        diff = deep_diff(a, b)
        self.assertEqual(diff["added"], {"y": 2})
        self.assertEqual(diff["removed"], {})
        self.assertEqual(diff["changed"], {})
    
    def test_removed_keys(self):
        """Test detection of removed keys."""
        a = {"x": 1, "y": 2}
        b = {"x": 1}
        diff = deep_diff(a, b)
        self.assertEqual(diff["added"], {})
        self.assertEqual(diff["removed"], {"y": 2})
        self.assertEqual(diff["changed"], {})
    
    def test_changed_values(self):
        """Test detection of changed values."""
        a = {"x": 1}
        b = {"x": 2}
        diff = deep_diff(a, b)
        self.assertEqual(diff["added"], {})
        self.assertEqual(diff["removed"], {})
        self.assertEqual(diff["changed"], {"x": {"old": 1, "new": 2}})
    
    def test_nested_diff(self):
        """Test nested structure diff."""
        a = {"outer": {"inner": 1}}
        b = {"outer": {"inner": 2}}
        diff = deep_diff(a, b)
        self.assertEqual(diff["changed"], {"outer.inner": {"old": 1, "new": 2}})
    
    def test_list_index_diff(self):
        """Test list index-based diff."""
        a = [1, 2, 3]
        b = [1, 5, 3]
        diff = deep_diff(a, b)
        self.assertEqual(diff["changed"], {"[1]": {"old": 2, "new": 5}})
    
    def test_list_length_diff(self):
        """Test list with different lengths."""
        a = [1, 2]
        b = [1, 2, 3]
        diff = deep_diff(a, b)
        self.assertEqual(diff["added"], {"[2]": 3})
    
    def test_list_shorter(self):
        """Test list that became shorter."""
        a = [1, 2, 3]
        b = [1, 2]
        diff = deep_diff(a, b)
        self.assertEqual(diff["removed"], {"[2]": 3})
    
    def test_complex_mixed_diff(self):
        """Test complex mixed structure diff."""
        a = {"list": [1, 2], "val": 10}
        b = {"list": [1, 3], "val": 10, "new": "x"}
        diff = deep_diff(a, b)
        self.assertEqual(diff["added"], {"new": "x"})
        self.assertEqual(diff["changed"], {"list[1]": {"old": 2, "new": 3}})
        self.assertEqual(diff["removed"], {})
    
    def test_empty_to_populated(self):
        """Test diff from empty to populated."""
        a = {}
        b = {"x": 1, "y": 2}
        diff = deep_diff(a, b)
        self.assertEqual(diff["added"], {"x": 1, "y": 2})
    
    def test_populated_to_empty(self):
        """Test diff from populated to empty."""
        a = {"x": 1, "y": 2}
        b = {}
        diff = deep_diff(a, b)
        self.assertEqual(diff["removed"], {"x": 1, "y": 2})
    
    def test_type_change(self):
        """Test type change detection."""
        a = {"x": 1}
        b = {"x": "1"}
        diff = deep_diff(a, b)
        self.assertIn("x", diff["changed"])
    
    def test_deep_nesting(self):
        """Test deeply nested structures."""
        a = {"a": {"b": {"c": {"d": 1}}}}
        b = {"a": {"b": {"c": {"d": 2}}}}
        diff = deep_diff(a, b)
        self.assertEqual(diff["changed"], {"a.b.c.d": {"old": 1, "new": 2}})
    
    def test_tuple_diff(self):
        """Test tuple diff (ordered)."""
        a = (1, 2, 3)
        b = (1, 5, 3)
        diff = deep_diff(a, b)
        self.assertEqual(diff["changed"], {"[1]": {"old": 2, "new": 5}})
    
    def test_set_diff(self):
        """Test set diff (unordered)."""
        a = {1, 2, 3}
        b = {1, 2, 4}
        diff = deep_diff(a, b)
        # 3 removed, 4 added
        self.assertTrue(any("3" in k for k in diff["removed"].keys()))
        self.assertTrue(any("4" in k for k in diff["added"].keys()))


if __name__ == "__main__":
    unittest.main()
