"""Pure-logic unit tests for ecnyss.util.functional."""
import unittest
from ecnyss.util.functional import (
    identity, constant, compose, pipe, curry, partial, flip
)

class TestIdentity(unittest.TestCase):
    def test_returns_same_value(self):
        self.assertEqual(identity(42), 42)
        self.assertEqual(identity("hello"), "hello")
        self.assertEqual(identity([1, 2]), [1, 2])
        self.assertIs(identity(None), None)

class TestConstant(unittest.TestCase):
    def test_always_returns_value(self):
        f = constant(99)
        self.assertEqual(f(), 99)
        self.assertEqual(f(1, 2, 3), 99)
        self.assertEqual(f(a=1, b=2), 99)

class TestCompose(unittest.TestCase):
    def test_empty_compose_is_identity(self):
        self.assertEqual(compose()(5), 5)

    def test_single_function(self):
        self.assertEqual(compose(lambda x: x * 2)(3), 6)

    def test_right_to_left(self):
        add1 = lambda x: x + 1
        mul2 = lambda x: x * 2
        # compose(mul2, add1)(3) == mul2(add1(3)) == mul2(4) == 8
        self.assertEqual(compose(mul2, add1)(3), 8)

    def test_three_functions(self):
        self.assertEqual(compose(str, lambda x: x * 2, lambda x: x + 1)(3), "8")

class TestPipe(unittest.TestCase):
    def test_empty_pipe_is_identity(self):
        self.assertEqual(pipe()(5), 5)

    def test_single_function(self):
        self.assertEqual(pipe(lambda x: x * 2)(3), 6)

    def test_left_to_right(self):
        add1 = lambda x: x + 1
        mul2 = lambda x: x * 2
        # pipe(add1, mul2)(3) == mul2(add1(3)) == mul2(4) == 8
        self.assertEqual(pipe(add1, mul2)(3), 8)

    def test_three_functions(self):
        self.assertEqual(pipe(lambda x: x + 1, lambda x: x * 2, str)(3), "8")

class TestCurry(unittest.TestCase):
    def test_curry_three_args(self):
        def add3(a: int, b: int, c: int) -> int:
            return a + b + c
        curried = curry(add3)
        self.assertEqual(curried(1)(2)(3), 6)
        self.assertEqual(curried(1, 2)(3), 6)
        self.assertEqual(curried(1)(2, 3), 6)
        self.assertEqual(curried(1, 2, 3), 6)

    def test_curry_with_kwargs(self):
        def greet(greeting: str, name: str) -> str:
            return f"{greeting}, {name}!"
        curried = curry(greet)
        self.assertEqual(curried("Hello")("World"), "Hello, World!")
        self.assertEqual(curried(greeting="Hi")(name="There"), "Hi, There!")

class TestPartial(unittest.TestCase):
    def test_partial_application(self):
        def mul(a: int, b: int, c: int) -> int:
            return a * b * c
        p = partial(mul, 2)
        self.assertEqual(p(3, 4), 24)
        p2 = partial(mul, 2, 3)
        self.assertEqual(p2(4), 24)

    def test_partial_with_kwargs(self):
        def fmt(prefix: str, value: int, suffix: str) -> str:
            return f"{prefix}{value}{suffix}"
        p = partial(fmt, prefix="[", suffix="]")
        self.assertEqual(p(42), "[42]")
    
    def test_partial_mixed_args_kwargs(self):
        def func(a: int, b: int, c: int, d: int) -> int:
            return a + b + c + d
        p = partial(func, 1, d=10)
        self.assertEqual(p(2, 3), 16)  # 1 + 2 + 3 + 10
    
    def test_partial_kwargs_override(self):
        def func(a: int, b: int) -> int:
            return a * b
        p = partial(func, a=5)
        self.assertEqual(p(b=3), 15)
        self.assertEqual(p(3), 15)
        # Call-time kwargs should override pre-bound
        self.assertEqual(p(b=10), 50)

class TestFlip(unittest.TestCase):
    def test_flips_two_args(self):
        def divide(a: int, b: int) -> float:
            return a / b
        flipped = flip(divide)
        self.assertEqual(flipped(10, 2), 0.2)  # 2 / 10
        self.assertEqual(flipped(2, 10), 5.0)  # 10 / 2

    def test_flip_with_strings(self):
        def concat(a: str, b: str) -> str:
            return a + b
        flipped = flip(concat)
        self.assertEqual(flipped("hello", "world"), "worldhello")

if __name__ == "__main__":
    unittest.main()
