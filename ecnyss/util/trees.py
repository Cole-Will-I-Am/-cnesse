"""Pure-stdlib nested-structure utilities (get_in, set_in, update_in, walk)."""

from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, TypeVar

T = TypeVar("T")
Path = Sequence[Any]  # e.g. ("a", 0, "b")


def get_in(data: Any, path: Path, default: T | None = None) -> Any | T:
    """Return value at `path` in nested `data` (dict/list/tuple), or `default` if missing."""
    cur = data
    for key in path:
        if isinstance(cur, Mapping) and key in cur:
            cur = cur[key]
        elif isinstance(cur, Sequence) and not isinstance(cur, (str, bytes)):
            try:
                cur = cur[key]
            except (IndexError, TypeError):
                return default
        else:
            return default
    return cur


def set_in(data: Any, path: Path, value: Any) -> Any:
    """Return a new structure with `value` set at `path` (immutable update)."""
    if not path:
        return value
    key, *rest = path
    if isinstance(data, Mapping):
        new = dict(data)
        new[key] = set_in(data.get(key, {}), rest, value) if rest else value
        return new
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        lst = list(data)
        if isinstance(key, int) and 0 <= key < len(lst):
            lst[key] = set_in(lst[key], rest, value) if rest else value
        else:
            raise IndexError(f"Index {key} out of range for sequence of length {len(lst)}")
        return type(data)(lst) if type(data) is not list else lst
    else:
        raise TypeError(f"Cannot set_in on non-container type {type(data).__name__}")


def update_in(data: Any, path: Path, func: Callable[[Any], Any]) -> Any:
    """Return new structure with `func` applied to value at `path` (immutable)."""
    current = get_in(data, path, _MISSING := object())
    if current is _MISSING:
        raise KeyError(f"Path {path} not found in data")
    return set_in(data, path, func(current))


def walk(data: Any) -> Iterable[tuple[Path, Any]]:
    """Yield (path, value) for every leaf in nested `data` (dict/list/tuple)."""
    def _walk(node: Any, prefix: Path) -> Iterable[tuple[Path, Any]]:
        if isinstance(node, Mapping):
            for k, v in node.items():
                yield from _walk(v, prefix + (k,))
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes)):
            for i, v in enumerate(node):
                yield from _walk(v, prefix + (i,))
        else:
            yield (prefix, node)
    yield from _walk(data, ())
