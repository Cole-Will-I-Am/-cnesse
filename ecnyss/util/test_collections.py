"""Unit tests for ecnyss.util.collections module."""

import unittest
from typing import List

from ecnyss.util.collections import chunk, flatten, unique_preserve_order, take


class TestChunk(unittest.TestCase):
    """Tests for the chunk function."""
    
    def test_chunk_empty_input(self):
        """Test chunking an empty iterable."""
        result = chunk([], 3)
        self.assertEqual(result, [])
    
    def test_chunk_size_one(self):
        """Test chunking with size=1."""
        result = chunk([1, 2, 3], 1)
        self.assertEqual(result, [[1], [2], [3]])
    
    def test_chunk_size_greater_than_len(self):
        """Test chunking when size > len(iterable)."""
        result = chunk([1, 2], 5)
        self.assertEqual(result, [[1, 2]])
    
    def test_chunk_normal_case(self):
        """Test normal chunking behavior."""
        result = chunk([1, 2, 3, 4, 5], 2)
        self.assertEqual(result, [[1, 2], [3, 4], [5]])
    
    def test_chunk_iterator_input(self):
        """Test chunking with generator/iterator input."""
        def gen():
            for i in range(5):
                yield i
        result = chunk(gen(), 2)
        self.assertEqual(result, [[0, 1], [2, 3], [4]])
    
    def test_chunk_invalid_size_zero(self):
        """Test that size=0 raises ValueError."""
        with self.assertRaises(ValueError):
            chunk([1, 2, 3], 0)
    
    def test_chunk_invalid_size_negative(self):
        """Test that negative size raises ValueError."""
        with self.assertRaises(ValueError):
            chunk([1, 2, 3], -1)
    
    def test_chunk_returns_list_of_lists(self):
        """Test that chunk returns list of lists."""
        result = chunk([1, 2, 3], 2)
        self.assertIsInstance(result, list)
        self.assertTrue(all(isinstance(chunk, list) for chunk in result))


class TestFlatten(unittest.TestCase):
    """Tests for the flatten function."""
    
    def test_flatten_empty_input(self):
        """Test flattening an empty iterable."""
        result = flatten([])
        self.assertEqual(result, [])
    
    def test_flatten_empty_inner_lists(self):
        """Test flattening with empty inner iterables."""
        result = flatten([[], [], []])
        self.assertEqual(result, [])
    
    def test_flatten_normal_case(self):
        """Test normal flattening behavior."""
        result = flatten([[1, 2], [3, 4], [5]])
        self.assertEqual(result, [1, 2, 3, 4, 5])
    
    def test_flatten_iterator_input(self):
        """Test flattening with generator input."""
        def gen():
            yield [1, 2]
            yield [3, 4]
        result = flatten(gen())
        self.assertEqual(result, [1, 2, 3, 4])
    
    def test_flatten_tuple_inner(self):
        """Test flattening with tuple inner iterables."""
        result = flatten([(1, 2), (3, 4)])
        self.assertEqual(result, [1, 2, 3, 4])


class TestUniquePreserveOrder(unittest.TestCase):
    """Tests for the unique_preserve_order function."""
    
    def test_unique_empty_input(self):
        """Test unique with empty iterable."""
        result = unique_preserve_order([])
        self.assertEqual(result, [])
    
    def test_unique_no_duplicates(self):
        """Test unique when there are no duplicates."""
        result = unique_preserve_order([1, 2, 3])
        self.assertEqual(result, [1, 2, 3])
    
    def test_unique_with_duplicates(self):
        """Test unique removes duplicates."""
        result = unique_preserve_order([1, 2, 2, 3, 1, 4])
        self.assertEqual(result, [1, 2, 3, 4])
    
    def test_unique_preserves_order(self):
        """Test that unique preserves first-occurrence order."""
        result = unique_preserve_order([3, 1, 2, 1, 3, 4])
        self.assertEqual(result, [3, 1, 2, 4])
    
    def test_unique_iterator_input(self):
        """Test unique with generator input."""
        def gen():
            for i in [1, 2, 2, 3]:
                yield i
        result = unique_preserve_order(gen())
        self.assertEqual(result, [1, 2, 3])


class TestTake(unittest.TestCase):
    """Tests for the take function."""
    
    def test_take_zero(self):
        """Test take with n=0."""
        result = take(0, [1, 2, 3])
        self.assertEqual(result, [])
    
    def test_take_one(self):
        """Test take with n=1."""
        result = take(1, [1, 2, 3])
        self.assertEqual(result, [1])
    
    def test_take_less_than_available(self):
        """Test take when n < len(iterable)."""
        result = take(2, [1, 2, 3, 4, 5])
        self.assertEqual(result, [1, 2])
    
    def test_take_more_than_available(self):
        """Test take when n > len(iterable)."""
        result = take(10, [1, 2, 3])
        self.assertEqual(result, [1, 2, 3])
    
    def test_take_empty_iterable(self):
        """Test take with empty iterable."""
        result = take(5, [])
        self.assertEqual(result, [])
    
    def test_take_iterator_input(self):
        """Test take with generator input."""
        def gen():
            for i in range(10):
                yield i
        result = take(3, gen())
        self.assertEqual(result, [0, 1, 2])
    
    def test_take_invalid_negative(self):
        """Test that negative n raises ValueError."""
        with self.assertRaises(ValueError):
            take(-1, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
