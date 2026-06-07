"""Unit tests for ecnyss.util.itertools module."""
import unittest
from typing import List, Iterator, Any, Optional

from ecnyss.util.itertools import batched, pairwise, sliding_window, consume


class TestBatched(unittest.TestCase):
    """Tests for the batched iterator utility."""
    
    def test_empty_iterable(self) -> None:
        """Batching an empty iterable yields nothing."""
        result = list(batched([], 3))
        self.assertEqual(result, [])
    
    def test_exact_multiple(self) -> None:
        """Batching when length is exact multiple of size."""
        result = list(batched([1, 2, 3, 4, 5, 6], 3))
        self.assertEqual(result, [(1, 2, 3), (4, 5, 6)])
    
    def test_partial_last_batch(self) -> None:
        """Last batch may be smaller than size."""
        result = list(batched([1, 2, 3, 4, 5], 3))
        self.assertEqual(result, [(1, 2, 3), (4, 5)])
    
    def test_size_one(self) -> None:
        """Batching with size 1 yields single-element tuples."""
        result = list(batched([1, 2, 3], 1))
        self.assertEqual(result, [(1,), (2,), (3,)])
    
    def test_size_larger_than_iterable(self) -> None:
        """Size larger than iterable yields single batch."""
        result = list(batched([1, 2], 10))
        self.assertEqual(result, [(1, 2)])
    
    def test_invalid_size_zero(self) -> None:
        """Size of 0 raises ValueError."""
        with self.assertRaises(ValueError):
            list(batched([1, 2, 3], 0))
    
    def test_invalid_size_negative(self) -> None:
        """Negative size raises ValueError."""
        with self.assertRaises(ValueError):
            list(batched([1, 2, 3], -1))
    
    def test_generator_input(self) -> None:
        """Works with generator input."""
        def gen():
            for i in range(5):
                yield i
        result = list(batched(gen(), 2))
        self.assertEqual(result, [(0, 1), (2, 3), (4,)])
    
    def test_string_input(self) -> None:
        """Works with string input."""
        result = list(batched("abcdef", 2))
        self.assertEqual(result, [('a', 'b'), ('c', 'd'), ('e', 'f')])


class TestPairwise(unittest.TestCase):
    """Tests for the pairwise iterator utility."""
    
    def test_empty_iterable(self) -> None:
        """Pairwise on empty iterable yields nothing."""
        result = list(pairwise([]))
        self.assertEqual(result, [])
    
    def test_single_element(self) -> None:
        """Pairwise on single element yields nothing."""
        result = list(pairwise([1]))
        self.assertEqual(result, [])
    
    def test_two_elements(self) -> None:
        """Pairwise on two elements yields one pair."""
        result = list(pairwise([1, 2]))
        self.assertEqual(result, [(1, 2)])
    
    def test_multiple_elements(self) -> None:
        """Pairwise yields overlapping consecutive pairs."""
        result = list(pairwise([1, 2, 3, 4]))
        self.assertEqual(result, [(1, 2), (2, 3), (3, 4)])
    
    def test_generator_input(self) -> None:
        """Works with generator input."""
        def gen():
            for i in range(4):
                yield i
        result = list(pairwise(gen()))
        self.assertEqual(result, [(0, 1), (1, 2), (2, 3)])
    
    def test_string_input(self) -> None:
        """Works with string input."""
        result = list(pairwise("abcd"))
        self.assertEqual(result, [('a', 'b'), ('b', 'c'), ('c', 'd')])
    
    def test_preserves_order(self) -> None:
        """Preserves element order in pairs."""
        result = list(pairwise([3, 1, 4, 1, 5]))
        self.assertEqual(result, [(3, 1), (1, 4), (4, 1), (1, 5)])


class TestSlidingWindow(unittest.TestCase):
    """Tests for the sliding_window iterator utility."""
    
    def test_empty_iterable(self) -> None:
        """Sliding window on empty iterable yields nothing."""
        result = list(sliding_window([], 3))
        self.assertEqual(result, [])
    
    def test_window_larger_than_iterable(self) -> None:
        """Window size larger than iterable yields nothing."""
        result = list(sliding_window([1, 2], 5))
        self.assertEqual(result, [])
    
    def test_window_equals_iterable(self) -> None:
        """Window size equals iterable length yields one window."""
        result = list(sliding_window([1, 2, 3], 3))
        self.assertEqual(result, [(1, 2, 3)])
    
    def test_multiple_windows(self) -> None:
        """Yields multiple overlapping windows."""
        result = list(sliding_window([1, 2, 3, 4, 5], 3))
        self.assertEqual(result, [(1, 2, 3), (2, 3, 4), (3, 4, 5)])
    
    def test_window_size_one(self) -> None:
        """Window size 1 yields single-element tuples."""
        result = list(sliding_window([1, 2, 3], 1))
        self.assertEqual(result, [(1,), (2,), (3,)])
    
    def test_invalid_size_zero(self) -> None:
        """Size of 0 raises ValueError."""
        with self.assertRaises(ValueError):
            list(sliding_window([1, 2, 3], 0))
    
    def test_invalid_size_negative(self) -> None:
        """Negative size raises ValueError."""
        with self.assertRaises(ValueError):
            list(sliding_window([1, 2, 3], -1))
    
    def test_generator_input(self) -> None:
        """Works with generator input."""
        def gen():
            for i in range(5):
                yield i
        result = list(sliding_window(gen(), 2))
        self.assertEqual(result, [(0, 1), (1, 2), (2, 3), (3, 4)])
    
    def test_string_input(self) -> None:
        """Works with string input."""
        result = list(sliding_window("abcde", 3))
        self.assertEqual(result, [('a', 'b', 'c'), ('b', 'c', 'd'), ('c', 'd', 'e')])


class TestConsume(unittest.TestCase):
    """Tests for the consume iterator utility."""
    
    def test_consume_zero(self) -> None:
        """Consuming 0 items leaves iterator unchanged."""
        it = iter([1, 2, 3, 4, 5])
        count = consume(it, 0)
        self.assertEqual(count, 0)
        self.assertEqual(list(it), [1, 2, 3, 4, 5])
    
    def test_consume_partial(self) -> None:
        """Consuming n items advances iterator by n."""
        it = iter([1, 2, 3, 4, 5])
        count = consume(it, 3)
        self.assertEqual(count, 3)
        self.assertEqual(list(it), [4, 5])
    
    def test_consume_all_explicit(self) -> None:
        """Consuming more than available consumes all."""
        it = iter([1, 2, 3])
        count = consume(it, 10)
        self.assertEqual(count, 3)
        self.assertEqual(list(it), [])
    
    def test_consume_exhaust(self) -> None:
        """Consuming with n=None exhausts iterator."""
        it = iter([1, 2, 3, 4, 5])
        count = consume(it, None)
        self.assertEqual(count, 5)
        self.assertEqual(list(it), [])
    
    def test_consume_empty(self) -> None:
        """Consuming from empty iterator returns 0."""
        it = iter([])
        count = consume(it, 5)
        self.assertEqual(count, 0)
    
    def test_consume_exhaust_empty(self) -> None:
        """Consuming None from empty iterator returns 0."""
        it = iter([])
        count = consume(it, None)
        self.assertEqual(count, 0)
    
    def test_consume_negative_raises(self) -> None:
        """Negative n raises ValueError."""
        it = iter([1, 2, 3])
        with self.assertRaises(ValueError):
            consume(it, -1)
    
    def test_consume_generator(self) -> None:
        """Works with generator input."""
        def gen():
            for i in range(10):
                yield i
        it = gen()
        count = consume(it, 5)
        self.assertEqual(count, 5)
        remaining = list(it)
        self.assertEqual(remaining, [5, 6, 7, 8, 9])
    
    def test_consume_returns_count(self) -> None:
        """Returns accurate count of consumed items."""
        it = iter(range(100))
        count = consume(it, 42)
        self.assertEqual(count, 42)


if __name__ == '__main__':
    unittest.main()
