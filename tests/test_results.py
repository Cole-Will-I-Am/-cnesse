"""Unit tests for ecnyss.util.results module."""

import unittest
from ecnyss.util.results import Result, Ok, Err


class TestOk(unittest.TestCase):
    """Tests for the Ok result type."""

    def test_is_ok_returns_true(self):
        ok = Ok(42)
        self.assertTrue(ok.is_ok())

    def test_is_err_returns_false(self):
        ok = Ok(42)
        self.assertFalse(ok.is_err())

    def test_unwrap_or_returns_value(self):
        ok = Ok(42)
        self.assertEqual(ok.unwrap_or(0), 42)

    def test_unwrap_or_ignores_default(self):
        ok = Ok("value")
        self.assertEqual(ok.unwrap_or("default"), "value")

    def test_map_applies_function(self):
        ok = Ok(5)
        result = ok.map(lambda x: x * 2)
        self.assertIsInstance(result, Ok)
        self.assertEqual(result.unwrap_or(0), 10)

    def test_map_preserves_type(self):
        ok = Ok(10)
        result = ok.map(str)
        self.assertIsInstance(result, Ok)
        self.assertEqual(result.unwrap_or(""), "10")

    def test_bind_applies_function(self):
        ok = Ok(5)
        result = ok.bind(lambda x: Ok(x * 3))
        self.assertIsInstance(result, Ok)
        self.assertEqual(result.unwrap_or(0), 15)

    def test_bind_can_return_err(self):
        ok = Ok(5)
        result = ok.bind(lambda x: Err("error"))
        self.assertIsInstance(result, Err)
        self.assertTrue(result.is_err())

    def test_eq_same_value(self):
        ok1 = Ok(42)
        ok2 = Ok(42)
        self.assertEqual(ok1, ok2)

    def test_eq_different_value(self):
        ok1 = Ok(42)
        ok2 = Ok(43)
        self.assertNotEqual(ok1, ok2)

    def test_eq_different_type(self):
        ok = Ok(42)
        err = Err(42)
        self.assertNotEqual(ok, err)

    def test_repr(self):
        ok = Ok(42)
        self.assertEqual(repr(ok), "Ok(42)")

    def test_repr_string(self):
        ok = Ok("hello")
        self.assertEqual(repr(ok), "Ok('hello')")


class TestErr(unittest.TestCase):
    """Tests for the Err result type."""

    def test_is_ok_returns_false(self):
        err = Err("error")
        self.assertFalse(err.is_ok())

    def test_is_err_returns_true(self):
        err = Err("error")
        self.assertTrue(err.is_err())

    def test_unwrap_or_returns_default(self):
        err = Err("error")
        self.assertEqual(err.unwrap_or(42), 42)

    def test_unwrap_or_with_none_default(self):
        err = Err("error")
        self.assertIsNone(err.unwrap_or(None))

    def test_map_returns_self(self):
        err = Err("error")
        result = err.map(lambda x: x * 2)
        self.assertIs(result, err)

    def test_map_does_not_apply_function(self):
        err = Err("error")
        result = err.map(lambda x: "transformed")
        self.assertIsInstance(result, Err)
        self.assertEqual(result.unwrap_or("default"), "default")

    def test_bind_returns_self(self):
        err = Err("error")
        result = err.bind(lambda x: Ok(x * 3))
        self.assertIs(result, err)

    def test_bind_preserves_error(self):
        err = Err("original_error")
        result = err.bind(lambda x: Ok(42))
        self.assertIsInstance(result, Err)
        self.assertEqual(result.unwrap_or("default"), "default")

    def test_eq_same_error(self):
        err1 = Err("error")
        err2 = Err("error")
        self.assertEqual(err1, err2)

    def test_eq_different_error(self):
        err1 = Err("error1")
        err2 = Err("error2")
        self.assertNotEqual(err1, err2)

    def test_eq_different_type(self):
        err = Err(42)
        ok = Ok(42)
        self.assertNotEqual(err, ok)

    def test_repr(self):
        err = Err("error")
        self.assertEqual(repr(err), "Err('error')")

    def test_repr_number(self):
        err = Err(42)
        self.assertEqual(repr(err), "Err(42)")


class TestResultChaining(unittest.TestCase):
    """Tests for chaining Result operations."""

    def test_chain_ok_operations(self):
        result = Ok(2).map(lambda x: x + 1).map(lambda x: x * 3)
        self.assertIsInstance(result, Ok)
        self.assertEqual(result.unwrap_or(0), 9)

    def test_chain_with_bind(self):
        result = Ok(2).bind(lambda x: Ok(x + 1)).bind(lambda x: Ok(x * 3))
        self.assertIsInstance(result, Ok)
        self.assertEqual(result.unwrap_or(0), 9)

    def test_chain_err_stops_execution(self):
        result = Ok(2).map(lambda x: x + 1).bind(lambda x: Err("stopped")).map(lambda x: x * 3)
        self.assertIsInstance(result, Err)
        self.assertTrue(result.is_err())

    def test_chain_multiple_errs(self):
        result = Err("first").map(lambda x: x + 1).bind(lambda x: Ok(x * 3))
        self.assertIsInstance(result, Err)
        self.assertEqual(result.unwrap_or("default"), "default")

    def test_complex_chain_ok(self):
        def safe_divide(x, y):
            if y == 0:
                return Err("division by zero")
            return Ok(x / y)

        result = Ok(10).bind(lambda x: safe_divide(x, 2)).map(lambda x: x + 5)
        self.assertIsInstance(result, Ok)
        self.assertEqual(result.unwrap_or(0), 10.0)

    def test_complex_chain_err(self):
        def safe_divide(x, y):
            if y == 0:
                return Err("division by zero")
            return Ok(x / y)

        result = Ok(10).bind(lambda x: safe_divide(x, 0)).map(lambda x: x + 5)
        self.assertIsInstance(result, Err)
        self.assertTrue(result.is_err())


class TestResultTypeSafety(unittest.TestCase):
    """Tests for Result type behavior."""

    def test_ok_with_none_value(self):
        ok = Ok(None)
        self.assertTrue(ok.is_ok())
        self.assertIsNone(ok.unwrap_or("default"))

    def test_err_with_none_error(self):
        err = Err(None)
        self.assertTrue(err.is_err())
        self.assertEqual(err.unwrap_or("default"), "default")

    def test_ok_with_empty_string(self):
        ok = Ok("")
        self.assertTrue(ok.is_ok())
        self.assertEqual(ok.unwrap_or("default"), "")

    def test_ok_with_zero(self):
        ok = Ok(0)
        self.assertTrue(ok.is_ok())
        self.assertEqual(ok.unwrap_or(1), 0)

    def test_ok_with_false(self):
        ok = Ok(False)
        self.assertTrue(ok.is_ok())
        self.assertFalse(ok.unwrap_or(True))

    def test_generic_type_vars(self):
        # Verify that Result can handle different types
        ok_int: Result[int, str] = Ok(42)
        ok_str: Result[str, int] = Ok("hello")
        err_str: Result[int, str] = Err("error")
        
        self.assertEqual(ok_int.unwrap_or(0), 42)
        self.assertEqual(ok_str.unwrap_or(""), "hello")
        self.assertEqual(err_str.unwrap_or(0), 0)


if __name__ == "__main__":
    unittest.main()
