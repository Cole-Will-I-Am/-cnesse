"""Pure-logic unit tests for ecnyss.util.trees."""

import unittest
from ecnyss.util.trees import get_in, set_in, update_in, walk


class TestGetIn(unittest.TestCase):
    def test_nested_dict(self):
        data = {"a": {"b": {"c": 42}}}
        self.assertEqual(get_in(data, ("a", "b", "c")), 42)
        self.assertEqual(get_in(data, ("a", "x"), "default"), "default")

    def test_nested_list(self):
        data = {"a": [{"b": 1}, {"b": 2}]}
        self.assertEqual(get_in(data, ("a", 0, "b")), 1)
        self.assertEqual(get_in(data, ("a", 1, "b")), 2)
        self.assertEqual(get_in(data, ("a", 5, "b"), "X"), "X")

    def test_mixed(self):
        data = {"users": [{"name": "Alice", "tags": ["a", "b"]}]}
        self.assertEqual(get_in(data, ("users", 0, "tags", 1)), "b")

    def test_empty_path(self):
        self.assertEqual(get_in({"x": 1}, ()), {"x": 1})


class TestSetIn(unittest.TestCase):
    def test_dict_immutability(self):
        orig = {"a": {"b": 1}}
        new = set_in(orig, ("a", "b"), 99)
        self.assertEqual(new["a"]["b"], 99)
        self.assertEqual(orig["a"]["b"], 1)  # unchanged

    def test_list_immutability(self):
        orig = {"a": [1, 2, 3]}
        new = set_in(orig, ("a", 1), 99)
        self.assertEqual(new["a"][1], 99)
        self.assertEqual(orig["a"][1], 2)

    def test_create_missing_dict_path(self):
        orig = {}
        new = set_in(orig, ("a", "b", "c"), 42)
        self.assertEqual(new, {"a": {"b": {"c": 42}}})

    def test_tuple_preserved(self):
        orig = {"a": (1, 2)}
        new = set_in(orig, ("a", 1), 99)
        self.assertIsInstance(new["a"], tuple)
        self.assertEqual(new["a"], (1, 99))

    def test_invalid_index_raises(self):
        with self.assertRaises(IndexError):
            set_in([1, 2], (5,), 99)


class TestUpdateIn(unittest.TestCase):
    def test_increment(self):
        data = {"a": {"b": 10}}
        new = update_in(data, ("a", "b"), lambda x: x + 1)
        self.assertEqual(new["a"]["b"], 11)

    def test_missing_path_raises(self):
        with self.assertRaises(KeyError):
            update_in({}, ("x",), lambda x: x)


class TestWalk(unittest.TestCase):
    def test_dict_only(self):
        data = {"a": 1, "b": {"c": 2}}
        paths = dict(walk(data))
        self.assertEqual(paths[("a",)], 1)
        self.assertEqual(paths[("b", "c")], 2)

    def test_list_and_mixed(self):
        data = {"items": [{"v": 1}, {"v": 2}]}
        paths = dict(walk(data))
        self.assertEqual(paths[("items", 0, "v")], 1)
        self.assertEqual(paths[("items", 1, "v")], 2)

    def test_empty_structures(self):
        self.assertEqual(list(walk({})), [])
        self.assertEqual(list(walk([])), [])
        self.assertEqual(list(walk(42)), [((), 42)])


if __name__ == "__main__":
    unittest.main()
