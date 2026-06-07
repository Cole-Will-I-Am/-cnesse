"""Pure-stdlib dictionary utilities."""

from __future__ import annotations
from collections.abc import Mapping
from typing import Any


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge `overlay` into `base`, returning a new dict.
    Non-dict values in overlay replace base values. Dict values are merged recursively.
    """
    result = dict(base)
    for k, v in overlay.items():
        if k in result and isinstance(result[k], Mapping) and isinstance(v, Mapping):
            result[k] = deep_merge(dict(result[k]), dict(v))
        else:
            result[k] = v
    return result


def pick(d: dict[str, Any], keys: set[str] | list[str]) -> dict[str, Any]:
    """Return a new dict containing only the specified keys (ignores missing)."""
    key_set = set(keys)
    return {k: v for k, v in d.items() if k in key_set}


def omit(d: dict[str, Any], keys: set[str] | list[str]) -> dict[str, Any]:
    """Return a new dict excluding the specified keys."""
    key_set = set(keys)
    return {k: v for k, v in d.items() if k not in key_set}


def flatten_keys(d: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """Flatten nested dict keys using `separator` (e.g. {'a': {'b': 1}} -> {'a.b': 1})."""
    out: dict[str, Any] = {}

    def _flatten(prefix: str, value: Any) -> None:
        if isinstance(value, Mapping):
            for k, v in value.items():
                _flatten(f"{prefix}{separator}{k}" if prefix else k, v)
        else:
            out[prefix] = value

    _flatten("", d)
    return out


__all__ = ["deep_merge", "pick", "omit", "flatten_keys"]
