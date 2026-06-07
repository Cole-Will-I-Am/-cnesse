"""Result type for error handling in ecnyss."""

from typing import Generic, TypeVar, Callable, Any

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


class Result(Generic[T, E]):
    """Base class for Result type."""
    pass


class Ok(Result[T, E]):
    """Represents a successful result with a value."""

    def __init__(self, value: T) -> None:
        self._value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap_or(self, default: U) -> T:
        return self._value

    def map(self, func: Callable[[T], U]) -> 'Ok[U, E]':
        return Ok(func(self._value))

    def bind(self, func: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        return func(self._value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Ok):
            return self._value == other._value
        return False

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"


class Err(Result[T, E]):
    """Represents an error result with an error value."""

    def __init__(self, error: E) -> None:
        self._error = error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap_or(self, default: U) -> U:
        return default

    def map(self, func: Callable[[T], U]) -> 'Err[T, E]':
        return self

    def bind(self, func: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        return self

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Err):
            return self._error == other._error
        return False

    def __repr__(self) -> str:
        return f"Err({self._error!r})"
