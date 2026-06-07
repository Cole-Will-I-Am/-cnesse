"""Interval utilities for ecnyss."""


def _normalize(interval):
    """Normalize an interval so that start <= end."""
    start, end = interval
    return (min(start, end), max(start, end))


def contains(interval, value):
    """Check if a value is contained within an interval (inclusive)."""
    start, end = _normalize(interval)
    return start <= value <= end


def overlap(interval1, interval2):
    """Check if two intervals overlap (including shared endpoints)."""
    start1, end1 = _normalize(interval1)
    start2, end2 = _normalize(interval2)
    return start1 <= end2 and start2 <= end1


def intersect(interval1, interval2):
    """Return the intersection of two intervals, or None if disjoint."""
    start1, end1 = _normalize(interval1)
    start2, end2 = _normalize(interval2)
    
    if not overlap(interval1, interval2):
        return None
    
    return (max(start1, start2), min(end1, end2))


def merge(intervals):
    """Merge overlapping or adjacent intervals into a minimal set."""
    if not intervals:
        return []
    
    # Normalize and sort intervals
    normalized = [_normalize(iv) for iv in intervals]
    normalized.sort(key=lambda x: x[0])
    
    merged = [normalized[0]]
    
    for current in normalized[1:]:
        last = merged[-1]
        # Check if current overlaps or is adjacent to last
        if current[0] <= last[1]:
            # Merge them
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    
    return merged


def union(intervals):
    """Alias for merge - compute the union of intervals."""
    return merge(intervals)
