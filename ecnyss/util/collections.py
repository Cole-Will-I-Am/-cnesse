"""Pure-stdlib collection utilities."""

from typing import Any, Iterable, List, TypeVar

T = TypeVar('T')


def chunk(iterable: Iterable[T], size: int) -> List[List[T]]:
    """Split an iterable into chunks of specified size.
    
    Args:
        iterable: Any iterable to chunk.
        size: Maximum size of each chunk (must be >= 1).
    
    Returns:
        List of lists, where each inner list has at most `size` elements.
    
    Raises:
        ValueError: If size < 1.
    """
    if size < 1:
        raise ValueError("size must be >= 1")
    
    result: List[List[T]] = []
    current_chunk: List[T] = []
    
    for item in iterable:
        current_chunk.append(item)
        if len(current_chunk) == size:
            result.append(current_chunk)
            current_chunk = []
    
    if current_chunk:
        result.append(current_chunk)
    
    return result


def flatten(nested_iterable: Iterable[Iterable[Any]]) -> List[Any]:
    """Flatten one level of nesting from an iterable of iterables.
    
    Args:
        nested_iterable: An iterable containing iterables.
    
    Returns:
        A flat list containing all elements from the nested structure.
    """
    result: List[Any] = []
    for inner in nested_iterable:
        for item in inner:
            result.append(item)
    return result


def unique_preserve_order(iterable: Iterable[T]) -> List[T]:
    """Return unique elements while preserving first-occurrence order.
    
    Args:
        iterable: Any iterable that may contain duplicates.
    
    Returns:
        List of unique elements in order of first appearance.
    """
    seen: set = set()
    result: List[T] = []
    
    for item in iterable:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result


def take(n: int, iterable: Iterable[T]) -> List[T]:
    """Take the first n elements from an iterable.
    
    Args:
        n: Number of elements to take (must be >= 0).
        iterable: Any iterable.
    
    Returns:
        List of the first n elements (or all if fewer than n exist).
    
    Raises:
        ValueError: If n < 0.
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    
    result: List[T] = []
    count = 0
    
    for item in iterable:
        if count >= n:
            break
        result.append(item)
        count += 1
    
    return result
