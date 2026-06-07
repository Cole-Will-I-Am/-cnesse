"""Pure-logic unit tests for ecnyss.util.intervals."""

import unittest
from ecnyss.util.intervals import contains, intersect, merge, overlap, union


class TestContains(unittest.TestCase):
    """Tests for the contains() function."""
    
    def test_value_inside_interval(self):
        """Test value strictly inside interval."""
        self.assertTrue(contains((0, 10), 5))
    
    def test_value_at_start(self):
        """Test value at start boundary (inclusive)."""
        self.assertTrue(contains((0, 10), 0))
    
    def test_value_at_end(self):
        """Test value at end boundary (inclusive)."""
        self.assertTrue(contains((0, 10), 10))
    
    def test_value_below_interval(self):
        """Test value below interval."""
        self.assertFalse(contains((0, 10), -1))
    
    def test_value_above_interval(self):
        """Test value above interval."""
        self.assertFalse(contains((0, 10), 11))
    
    def test_single_point_interval(self):
        """Test single-point interval."""
        self.assertTrue(contains((5, 5), 5))
        self.assertFalse(contains((5, 5), 4))
        self.assertFalse(contains((5, 5), 6))
    
    def test_reversed_endpoints(self):
        """Test interval with reversed endpoints (should normalize)."""
        self.assertTrue(contains((10, 0), 5))
        self.assertTrue(contains((10, 0), 0))
        self.assertTrue(contains((10, 0), 10))
    
    def test_float_values(self):
        """Test with float values."""
        self.assertTrue(contains((0.0, 1.0), 0.5))
        self.assertTrue(contains((0.0, 1.0), 0.0))
        self.assertTrue(contains((0.0, 1.0), 1.0))


class TestOverlap(unittest.TestCase):
    """Tests for the overlap() function."""
    
    def test_overlapping_intervals(self):
        """Test intervals that overlap."""
        self.assertTrue(overlap((0, 10), (5, 15)))
    
    def test_contained_interval(self):
        """Test one interval contained in another."""
        self.assertTrue(overlap((0, 10), (2, 8)))
        self.assertTrue(overlap((2, 8), (0, 10)))
    
    def test_shared_endpoint(self):
        """Test intervals sharing an endpoint (adjacent)."""
        self.assertTrue(overlap((0, 10), (10, 20)))
        self.assertTrue(overlap((0, 10), (5, 10)))
    
    def test_disjoint_intervals(self):
        """Test intervals that don't overlap."""
        self.assertFalse(overlap((0, 5), (10, 15)))
    
    def test_single_point_overlap(self):
        """Test single-point intervals."""
        self.assertTrue(overlap((5, 5), (5, 5)))
        self.assertFalse(overlap((5, 5), (6, 6)))
    
    def test_reversed_endpoints(self):
        """Test intervals with reversed endpoints."""
        self.assertTrue(overlap((10, 0), (5, 15)))
        self.assertFalse(overlap((10, 0), (20, 15)))
    
    def test_empty_like_interval(self):
        """Test with zero-width intervals."""
        self.assertTrue(overlap((0, 0), (0, 0)))
        self.assertFalse(overlap((0, 0), (1, 1)))


class TestIntersect(unittest.TestCase):
    """Tests for the intersect() function."""
    
    def test_overlapping_intervals(self):
        """Test intersection of overlapping intervals."""
        self.assertEqual(intersect((0, 10), (5, 15)), (5, 10))
    
    def test_contained_interval(self):
        """Test intersection when one contains the other."""
        self.assertEqual(intersect((0, 10), (2, 8)), (2, 8))
        self.assertEqual(intersect((2, 8), (0, 10)), (2, 8))
    
    def test_shared_endpoint(self):
        """Test intersection at shared endpoint."""
        self.assertEqual(intersect((0, 10), (10, 20)), (10, 10))
    
    def test_disjoint_intervals(self):
        """Test intersection of disjoint intervals."""
        self.assertIsNone(intersect((0, 5), (10, 15)))
    
    def test_identical_intervals(self):
        """Test intersection of identical intervals."""
        self.assertEqual(intersect((0, 10), (0, 10)), (0, 10))
    
    def test_single_point_intersection(self):
        """Test intersection involving single points."""
        self.assertEqual(intersect((5, 5), (5, 5)), (5, 5))
        self.assertIsNone(intersect((5, 5), (6, 6)))
    
    def test_reversed_endpoints(self):
        """Test intervals with reversed endpoints."""
        self.assertEqual(intersect((10, 0), (5, 15)), (5, 10))
    
    def test_empty_input(self):
        """Test edge case with zero-width intervals."""
        self.assertEqual(intersect((0, 0), (0, 5)), (0, 0))


class TestMerge(unittest.TestCase):
    """Tests for the merge() function."""
    
    def test_empty_list(self):
        """Test merging empty list."""
        self.assertEqual(merge([]), [])
    
    def test_single_interval(self):
        """Test merging single interval."""
        self.assertEqual(merge([(0, 10)]), [(0, 10)])
    
    def test_disjoint_intervals(self):
        """Test merging disjoint intervals (no change expected)."""
        result = merge([(0, 5), (10, 15)])
        self.assertEqual(result, [(0, 5), (10, 15)])
    
    def test_overlapping_intervals(self):
        """Test merging overlapping intervals."""
        result = merge([(0, 10), (5, 15)])
        self.assertEqual(result, [(0, 15)])
    
    def test_adjacent_intervals_should_merge(self):
        """Test merging adjacent intervals (touching endpoints).
        
        This test exposes the Codex P2 defect: adjacent intervals should merge
        but may not due to implementation bug.
        """
        # Adjacent: [0, 5] and [5, 10] should merge to [0, 10]
        result = merge([(0, 5), (5, 10)])
        self.assertEqual(result, [(0, 10)])
    
    def test_adjacent_intervals_multiple(self):
        """Test merging multiple adjacent intervals.
        
        This test exposes the Codex P2 defect.
        """
        # Three adjacent intervals should merge to one
        result = merge([(0, 5), (5, 10), (10, 15)])
        self.assertEqual(result, [(0, 15)])
    
    def test_mixed_overlapping_and_adjacent(self):
        """Test merging mix of overlapping and adjacent intervals."""
        result = merge([(0, 5), (5, 10), (12, 15), (15, 20)])
        self.assertEqual(result, [(0, 10), (12, 20)])
    
    def test_unsorted_intervals(self):
        """Test merging unsorted intervals."""
        result = merge([(10, 15), (0, 5), (5, 10)])
        self.assertEqual(result, [(0, 15)])
    
    def test_reversed_endpoints_in_list(self):
        """Test merging intervals with reversed endpoints."""
        result = merge([(10, 0), (5, 15)])
        self.assertEqual(result, [(0, 15)])
    
    def test_single_point_intervals(self):
        """Test merging single-point intervals."""
        # Adjacent single points
        result = merge([(5, 5), (5, 5)])
        self.assertEqual(result, [(5, 5)])
        
        # Single point at boundary
        result = merge([(0, 5), (5, 5)])
        self.assertEqual(result, [(0, 5)])
    
    def test_nested_intervals(self):
        """Test merging nested intervals."""
        result = merge([(0, 20), (5, 10)])
        self.assertEqual(result, [(0, 20)])
    
    def test_all_same_interval(self):
        """Test merging identical intervals."""
        result = merge([(0, 10), (0, 10), (0, 10)])
        self.assertEqual(result, [(0, 10)])


class TestUnion(unittest.TestCase):
    """Tests for the union() function (alias for merge)."""
    
    def test_union_empty(self):
        """Test union of empty list."""
        self.assertEqual(union([]), [])
    
    def test_union_overlapping(self):
        """Test union of overlapping intervals."""
        self.assertEqual(union([(0, 10), (5, 15)]), [(0, 15)])
    
    def test_union_adjacent(self):
        """Test union of adjacent intervals.
        
        This test exposes the Codex P2 defect.
        """
        self.assertEqual(union([(0, 5), (5, 10)]), [(0, 10)])
    
    def test_union_disjoint(self):
        """Test union of disjoint intervals."""
        self.assertEqual(union([(0, 5), (10, 15)]), [(0, 5), (10, 15)])


if __name__ == "__main__":
    unittest.main()
