"""Iterator utilities for ecnyss.

This module provides pure-stdlib iterator utilities similar to itertools
recipes, including batched, pairwise, sliding_window, and consume.
"""
from typing import Iterator, Iterable, Tuple, Any, Optional, TypeVar

T = TypeVar('T')


def batched(iterable: Iterable[T], size: int) -> Iterator[Tuple[T, ...]]:
    """Batch data from the iterable into tuples of length size.
    
    The last batch may be shorter than size.
    
    Args:
        iterable: The input iterable to batch.
        size: The maximum size of each batch (must be >= 1).
        
    Yields:
        Tuples of up to `size` elements from the iterable.
        
    Raises:
        ValueError: If size is less than 1.
        
    Examples:
        >>> list(batched([1, 2, 3, 4, 5], 2))
        [(1, 2), (3, 4), (5,)]
    """
    if size < 1:
        raise ValueError("size must be >= 1")
    
    batch: list[T] = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield tuple(batch)
            batch = []
    
    if batch:
        yield tuple(batch)


def pairwise(iterable: Iterable[T]) -> Iterator[Tuple[T, T]]:
    """Yield overlapping consecutive pairs from the iterable.
    
    Args:
        iterable: The input iterable.
        
    Yields:
        Tuples of (current, next) elements.
        
    Examples:
        >>> list(pairwise([1, 2, 3, 4]))
        [(1, 2), (2, 3), (3, 4)]
    """
    it = iter(iterable)
    try:
        prev = next(it)
    except StopIteration:
        return
    
    for current in it:
        yield (prev, current)
        prev = current


def sliding_window(iterable: Iterable[T], size: int) -> Iterator[Tuple[T, ...]]:
    """Yield overlapping sliding windows of the given size.
    
    Args:
        iterable: The input iterable.
        size: The size of each window (must be >= 1).
        
    Yields:
        Tuples of `size` consecutive elements.
        
    Raises:
        ValueError: If size is less than 1.
        
    Examples:
        >>> list(sliding_window([1, 2, 3, 4, 5], 3))
        [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
    """
    if size < 1:
        raise ValueError("size must be >= 1")
    
    it = iter(iterable)
    window: list[T] = []
    
    # Fill initial window
    for item in it:
        window.append(item)
        if len(window) == size:
            yield tuple(window)
            break
    else:
        # Iterable exhausted before filling window
        return
    
    # Slide the window
    for item in it:
        window = window[1:] + [item]
        yield tuple(window)


def consume(iterator: Iterator[T], n: Optional[int]) -> int:
    """Advance the iterator n-steps ahead, consuming items.
    
    If n is None, consume to exhaustion.
    
    Args:
        iterator: The iterator to consume from.
        n: Number of items to consume, or None to consume all.
        
    Returns:
        The number of items actually consumed.
        
    Raises:
        ValueError: If n is negative.
        
    Examples:
        >>> it = iter([1, 2, 3, 4, 5])
        >>> consume(it, 3)
        3
        >>> list(it)
        [4, 5]
    """
    if n is not None and n < 0:
        raise ValueError("n must be >= 0 or None")
    
    count = 0
    if n is None:
        # Consume to exhaustion
        for _ in iterator:
            count += 1
    else:
        # Consume exactly n items (or until exhausted)
        for _ in range(n):
            try:
                next(iterator)
                count += 1
            except StopIteration:
                break
    
    return count
