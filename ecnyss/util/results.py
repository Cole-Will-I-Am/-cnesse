"""Result types for functional error handling in ecnyss.

Provides Ok/Err monadic types inspired by Rust's Result type.
"""

from __future__ import annotations
from typing import Any, Callable, Generic, TypeVar, Optional

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


class Result(Generic[T, E]):
    """Base class for Result types (Ok and Err).
    
    Result is a monadic type for handling computations that may fail.
    It provides methods for chaining operations while propagating errors.
    """
    
    __match_args__ = ('_value',)
    
    def is_ok(self) -> bool:
        """Return True if this Result is Ok."""
        raise NotImplementedError
    
    def is_err(self) -> bool:
        """Return True if this Result is Err."""
        raise NotImplementedError
    
    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        """Apply a function to the Ok value, if present.
        
        If this Result is Ok, apply fn to the value and return Ok(fn(value)).
        If this Result is Err, return the Err unchanged.
        
        Args:
            fn: A function to apply to the Ok value.
            
        Returns:
            A new Result with the transformed value, or the original Err.
        """
        raise NotImplementedError
    
    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Chain a function that returns a Result.
        
        If this Result is Ok, apply fn to the value and return the Result.
        If this Result is Err, return the Err unchanged (short-circuit).
        
        Args:
            fn: A function that takes the Ok value and returns a Result.
            
        Returns:
            The Result returned by fn, or the original Err.
        """
        raise NotImplementedError
    
    def unwrap(self) -> T:
        """Return the Ok value, or raise an exception if Err.
        
        Returns:
            The value contained in this Ok Result.
            
        Raises:
            Exception: If this Result is Err, raises the contained error.
        """
        raise NotImplementedError
    
    def unwrap_or(self, default: Any) -> Any:
        """Return the Ok value, or a default if Err.
        
        Args:
            default: The value to return if this Result is Err.
            
        Returns:
            The Ok value, or the default if Err.
        """
        raise NotImplementedError
    
    def __eq__(self, other: Any) -> bool:
        raise NotImplementedError
    
    def __hash__(self) -> int:
        raise NotImplementedError
    
    def __repr__(self) -> str:
        raise NotImplementedError


class Ok(Result[T, E]):
    """Represents a successful result containing a value.
    
    Args:
        value: The successful value.
    """
    
    __match_args__ = ('_value',)
    
    def __init__(self, value: T) -> None:
        self._value = value
    
    def is_ok(self) -> bool:
        return True
    
    def is_err(self) -> bool:
        return False
    
    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        try:
            return Ok(fn(self._value))
        except Exception as e:
            return Err(e)
    
    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        try:
            return fn(self._value)
        except Exception as e:
            return Err(e)
    
    def unwrap(self) -> T:
        return self._value
    
    def unwrap_or(self, default: Any) -> Any:
        return self._value
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Ok):
            return self._value == other._value
        return False
    
    def __hash__(self) -> int:
        return hash(('Ok', self._value))
    
    def __repr__(self) -> str:
        return f"Ok({self._value!r})"


class Err(Result[T, E]):
    """Represents a failed result containing an error.
    
    Args:
        error: The error value.
    """
    
    __match_args__ = ('_value',)
    
    def __init__(self, error: E) -> None:
        self._value = error
    
    def is_ok(self) -> bool:
        return False
    
    def is_err(self) -> bool:
        return True
    
    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        # Err passes through unchanged
        return self
    
    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        # Err passes through unchanged (short-circuit)
        return self
    
    def unwrap(self) -> T:
        # Raise the contained error
        if isinstance(self._value, BaseException):
            raise self._value
        raise Exception(self._value)
    
    def unwrap_or(self, default: Any) -> Any:
        return default
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Err):
            return self._value == other._value
        return False
    
    def __hash__(self) -> int:
        return hash(('Err', self._value))
    
    def __repr__(self) -> str:
        return f"Err({self._value!r})"


# Convenience aliases
Success = Ok
Failure = Err
