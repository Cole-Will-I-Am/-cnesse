"""Pure-stdlib numeric primitives for ecnyss."""

from __future__ import annotations
import math

__all__ = [
    "clamp", "sign", "lerp", "normalize", "remap", "round_to", "is_close",
]

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to [min_val, max_val]."""
    if min_val > max_val:
        raise ValueError("min_val must be <= max_val")
    return max(min_val, min(value, max_val))

def sign(x: float) -> int:
    """Return -1, 0, or 1 for negative, zero, positive."""
    return (x > 0) - (x < 0)

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation: a + t * (b - a)."""
    return a + t * (b - a)

def normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize value to [0, 1] given input range."""
    if min_val == max_val:
        raise ValueError("min_val and max_val must differ")
    return (value - min_val) / (max_val - min_val)

def remap(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Remap value from [in_min, in_max] to [out_min, out_max]."""
    return lerp(out_min, out_max, normalize(value, in_min, in_max))

def round_to(value: float, precision: int) -> float:
    """Round to `precision` decimal places (precision >= 0)."""
    if precision < 0:
        raise ValueError("precision must be >= 0")
    factor = 10 ** precision
    return math.floor(value * factor + 0.5) / factor if value >= 0 else math.ceil(value * factor - 0.5) / factor

def is_close(a: float, b: float, *, rel_tol: float = 1e-9, abs_tol: float = 0.0) -> bool:
    """Float comparison with relative and absolute tolerance (PEP 485).

    Delegates to math.isclose so infinities are handled correctly
    (inf is close only to itself, never to a finite value).
    """
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
