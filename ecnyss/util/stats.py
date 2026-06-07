"""Pure-stdlib descriptive statistics functions for Ecnyss."""
from typing import Sequence
import math


def _sort(data: Sequence[float]) -> list[float]:
    """Manual implementation of sorting (merge sort)."""
    if len(data) <= 1:
        return list(data)
    
    mid = len(data) // 2
    left = _sort(data[:mid])
    right = _sort(data[mid:])
    
    return _merge(left, right)


def _merge(left: list[float], right: list[float]) -> list[float]:
    """Merge two sorted lists."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result


def mean(data: Sequence[float]) -> float:
    """Calculate the arithmetic mean of the data."""
    if len(data) == 0:
        raise ValueError("Cannot calculate mean of empty sequence")
    
    total = 0.0
    for value in data:
        total += value
    
    return total / len(data)


def median(data: Sequence[float]) -> float:
    """Calculate the median of the data."""
    if len(data) == 0:
        raise ValueError("Cannot calculate median of empty sequence")
    
    sorted_data = _sort(data)
    n = len(sorted_data)
    
    if n % 2 == 1:
        return sorted_data[n // 2]
    else:
        mid = n // 2
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2


def variance(data: Sequence[float], ddof: int = 0) -> float:
    """Calculate the variance of the data.
    
    Args:
        data: Sequence of float values
        ddof: Delta degrees of freedom (0 for population, 1 for sample)
    
    Returns:
        Variance value
    
    Raises:
        ValueError: If data is empty or ddof >= len(data)
    """
    if len(data) == 0:
        raise ValueError("Cannot calculate variance of empty sequence")
    
    if ddof >= len(data):
        raise ValueError("ddof must be less than the number of data points")
    
    m = mean(data)
    squared_diff_sum = 0.0
    for value in data:
        squared_diff_sum += (value - m) ** 2
    
    return squared_diff_sum / (len(data) - ddof)


def stdev(data: Sequence[float], ddof: int = 0) -> float:
    """Calculate the standard deviation of the data.
    
    Args:
        data: Sequence of float values
        ddof: Delta degrees of freedom (0 for population, 1 for sample)
    
    Returns:
        Standard deviation value
    
    Raises:
        ValueError: If data is empty or ddof >= len(data)
    """
    return math.sqrt(variance(data, ddof))


def percentile(data: Sequence[float], p: float) -> float:
    """Calculate the p-th percentile of the data.
    
    Args:
        data: Sequence of float values
        p: Percentile value in range [0, 100]
    
    Returns:
        The p-th percentile value
    
    Raises:
        ValueError: If data is empty or p is out of bounds
    """
    if len(data) == 0:
        raise ValueError("Cannot calculate percentile of empty sequence")
    
    if p < 0 or p > 100:
        raise ValueError("Percentile p must be in range [0, 100]")
    
    sorted_data = _sort(data)
    n = len(sorted_data)
    
    if n == 1:
        return sorted_data[0]
    
    # Linear interpolation method
    k = (p / 100) * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)
    
    if f == c:
        return sorted_data[int(k)]
    
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    
    return d0 + d1


def quantile(data: Sequence[float], q: float) -> float:
    """Calculate the q-th quantile of the data.
    
    Args:
        data: Sequence of float values
        q: Quantile value in range [0, 1]
    
    Returns:
        The q-th quantile value
    
    Raises:
        ValueError: If data is empty or q is out of bounds
    """
    if q < 0 or q > 1:
        raise ValueError("Quantile q must be in range [0, 1]")
    
    return percentile(data, q * 100)


def min_max(data: Sequence[float]) -> tuple[float, float]:
    """Calculate the minimum and maximum of the data.
    
    Args:
        data: Sequence of float values
    
    Returns:
        Tuple of (min, max)
    
    Raises:
        ValueError: If data is empty
    """
    if len(data) == 0:
        raise ValueError("Cannot calculate min_max of empty sequence")
    
    min_val = data[0]
    max_val = data[0]
    
    for value in data[1:]:
        if value < min_val:
            min_val = value
        if value > max_val:
            max_val = value
    
    return (min_val, max_val)


def sum(data: Sequence[float]) -> float:
    """Calculate the sum of the data.
    
    Args:
        data: Sequence of float values
    
    Returns:
        Sum of all values (0.0 for empty sequence)
    """
    total = 0.0
    for value in data:
        total += value
    return total


def count(data: Sequence[float]) -> int:
    """Count the number of elements in the data.
    
    Args:
        data: Sequence of float values
    
    Returns:
        Number of elements (0 for empty sequence)
    """
    return len(data)
