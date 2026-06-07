"""Pure-stdlib functional composition utilities."""
from __future__ import annotations
from functools import partial as _stdlib_partial
from typing import Any, Callable, TypeVar
import inspect

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

def identity(x: T) -> T:
    """Return the argument unchanged."""
    return x

def constant(value: T) -> Callable[..., T]:
    """Return a function that always returns `value`."""
    return lambda *_, **__: value

def compose(*fns: Callable[..., Any]) -> Callable[..., Any]:
    """Right-to-left function composition: compose(f, g)(x) == f(g(x))."""
    if not fns:
        return identity
    def composed(*args: Any, **kwargs: Any) -> Any:
        result = fns[-1](*args, **kwargs)
        for fn in reversed(fns[:-1]):
            result = fn(result)
        return result
    return composed

def pipe(*fns: Callable[..., Any]) -> Callable[..., Any]:
    """Left-to-right function composition: pipe(f, g)(x) == g(f(x))."""
    if not fns:
        return identity
    def piped(*args: Any, **kwargs: Any) -> Any:
        result = fns[0](*args, **kwargs)
        for fn in fns[1:]:
            result = fn(result)
        return result
    return piped

def curry(fn: Callable[..., T]) -> Callable[..., Any]:
    """Curry a function: curry(f)(a)(b)(c) == f(a, b, c)."""
    def curried(*args: Any, **kwargs: Any) -> Any:
        if len(args) + len(kwargs) >= fn.__code__.co_argcount:
            return fn(*args, **kwargs)
        return lambda *more_args, **more_kwargs: curried(*args, *more_args, **{**kwargs, **more_kwargs})
    return curried

def partial(fn: Callable[..., T], *args: Any, **kwargs: Any) -> Callable[..., T]:
    """Partial application with smart keyword argument handling.
    
    Unlike functools.partial, this version skips parameters that are already
    bound by keyword arguments when assigning new positional arguments.
    This allows patterns like:
        p = partial(fmt, prefix="[", suffix="]")
        p(42)  # correctly binds 42 to 'value', not 'prefix'
    """
    try:
        sig = inspect.signature(fn)
        param_names = [name for name in sig.parameters.keys()]
    except (ValueError, TypeError):
        # Fall back to stdlib partial for functions we can't inspect
        return _stdlib_partial(fn, *args, **kwargs)
    
    # Track which params are already bound by kwargs
    kwarg_bound = set(kwargs.keys())
    
    def partial_fn(*more_args: Any, **more_kwargs: Any) -> T:
        # Merge kwargs (call-time kwargs override pre-bound)
        final_kwargs = {**kwargs, **more_kwargs}
        
        # Build final positional args list
        final_args = list(args)
        
        # Map more_args to unbound positional params in order
        positional_idx = len(args)
        for arg in more_args:
            # Find the next unbound param
            while positional_idx < len(param_names) and param_names[positional_idx] in kwarg_bound:
                positional_idx += 1
            if positional_idx < len(param_names):
                param_name = param_names[positional_idx]
                if param_name not in final_kwargs:
                    final_kwargs[param_name] = arg
                else:
                    final_args.append(arg)
                positional_idx += 1
            else:
                final_args.append(arg)
        
        return fn(*final_args, **final_kwargs)
    
    # Preserve function metadata
    partial_fn.__name__ = getattr(fn, '__name__', 'partial')
    partial_fn.__doc__ = getattr(fn, '__doc__', None)
    
    return partial_fn

def flip(fn: Callable[[T, U], V]) -> Callable[[U, T], V]:
    """Flip the first two arguments of a binary function."""
    return lambda a, b: fn(b, a)
