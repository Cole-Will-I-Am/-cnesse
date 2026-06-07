"""
Pure-stdlib predicate combinators and factories.
All functions are stateless, side-effect-free, and use only the standard library.
"""
from __future__ import annotations
import re
from collections.abc import Callable, Collection, Sequence
from typing import Any, TypeVar

T = TypeVar("T")
Predicate = Callable[[T], bool]


def all_of(*predicates: Predicate[T]) -> Predicate[T]:
    """Return a predicate that is True iff all given predicates are True."""
    def _all(x: T) -> bool:
        return all(p(x) for p in predicates)
    return _all


def any_of(*predicates: Predicate[T]) -> Predicate[T]:
    """Return a predicate that is True iff any given predicate is True."""
    def _any(x: T) -> bool:
        return any(p(x) for p in predicates)
    return _any


def none_of(*predicates: Predicate[T]) -> Predicate[T]:
    """Return a predicate that is True iff no given predicate is True."""
    def _none(x: T) -> bool:
        return not any(p(x) for p in predicates)
    return _none


def complement(predicate: Predicate[T]) -> Predicate[T]:
    """Return the logical negation of a predicate."""
    def _not(x: T) -> bool:
        return not predicate(x)
    return _not


def is_truthy(x: Any) -> bool:
    """Return True if x is truthy."""
    return bool(x)


def is_falsy(x: Any) -> bool:
    """Return True if x is falsy."""
    return not bool(x)


def equals(expected: T) -> Predicate[T]:
    """Return a predicate that checks equality to `expected`."""
    return lambda x: x == expected


def matches(pattern: str, flags: int = 0) -> Predicate[str]:
    """Return a predicate that checks if a string matches the regex pattern."""
    compiled = re.compile(pattern, flags)
    return lambda s: bool(compiled.search(s))


def in_range(min_val: T, max_val: T, *, inclusive: bool = True) -> Predicate[T]:
    """Return a predicate that checks if a value is within [min_val, max_val]."""
    if inclusive:
        return lambda x: min_val <= x <= max_val
    return lambda x: min_val < x < max_val


def has_length(expected: int) -> Predicate[Sequence[Any] | Collection[Any]]:
    """Return a predicate that checks if a sequence/collection has the given length."""
    return lambda x: len(x) == expected


def has_keys(*keys: str) -> Predicate[dict[str, Any]]:
    """Return a predicate that checks if a dict contains all given keys."""
    key_set = set(keys)
    return lambda d: key_set.issubset(d.keys())


def is_instance(*types: type) -> Predicate[Any]:
    """Return a predicate that checks if a value is an instance of any given type."""
    return lambda x: isinstance(x, types)
