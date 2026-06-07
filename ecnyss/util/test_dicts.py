"""Pure-logic unit tests for ecnyss.util.dicts."""

import pytest
from ecnyss.util.dicts import deep_merge, pick, omit, flatten_keys


class TestDeepMerge:
    def test_simple_override(self):
        assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_add_new_key(self):
        assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_nested_merge(self):
        base = {"a": {"x": 1}}
        overlay = {"a": {"y": 2}}
        assert deep_merge(base, overlay) == {"a": {"x": 1, "y": 2}}

    def test_nested_override(self):
        base = {"a": {"x": 1}}
        overlay = {"a": {"x": 99}}
        assert deep_merge(base, overlay) == {"a": {"x": 99}}

    def test_deep_nesting(self):
        base = {"a": {"b": {"c": 1}}}
        overlay = {"a": {"b": {"d": 2}}}
        assert deep_merge(base, overlay) == {"a": {"b": {"c": 1, "d": 2}}}

    def test_non_dict_overlay_replaces(self):
        assert deep_merge({"a": {"x": 1}}, {"a": "scalar"}) == {"a": "scalar"}

    def test_originals_unchanged(self):
        base = {"a": {"x": 1}}
        overlay = {"a": {"y": 2}}
        deep_merge(base, overlay)
        assert base == {"a": {"x": 1}}
        assert overlay == {"a": {"y": 2}}


class TestPick:
    def test_pick_existing(self):
        assert pick({"a": 1, "b": 2, "c": 3}, ["a", "c"]) == {"a": 1, "c": 3}

    def test_pick_with_set(self):
        assert pick({"a": 1, "b": 2}, {"b"}) == {"b": 2}

    def test_pick_missing_keys_ignored(self):
        assert pick({"a": 1}, ["a", "missing"]) == {"a": 1}

    def test_pick_empty_keys(self):
        assert pick({"a": 1}, []) == {}

    def test_pick_empty_dict(self):
        assert pick({}, ["a"]) == {}


class TestOmit:
    def test_omit_existing(self):
        assert omit({"a": 1, "b": 2, "c": 3}, ["b"]) == {"a": 1, "c": 3}

    def test_omit_with_set(self):
        assert omit({"a": 1, "b": 2}, {"a"}) == {"b": 2}

    def test_omit_missing_keys_ignored(self):
        assert omit({"a": 1}, ["missing"]) == {"a": 1}

    def test_omit_all_keys(self):
        assert omit({"a": 1, "b": 2}, ["a", "b"]) == {}

    def test_omit_empty_keys(self):
        assert omit({"a": 1}, []) == {"a": 1}


class TestFlattenKeys:
    def test_flat_dict_unchanged(self):
        assert flatten_keys({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_single_nesting(self):
        assert flatten_keys({"a": {"b": 1}}) == {"a.b": 1}

    def test_multi_level_nesting(self):
        assert flatten_keys({"a": {"b": {"c": 1}}}) == {"a.b.c": 1}

    def test_sibling_nesting(self):
        assert flatten_keys({"a": {"x": 1}, "b": {"y": 2}}) == {"a.x": 1, "b.y": 2}

    def test_mixed_flat_and_nested(self):
        assert flatten_keys({"a": 1, "b": {"c": 2}}) == {"a": 1, "b.c": 2}

    def test_custom_separator(self):
        assert flatten_keys({"a": {"b": 1}}, separator="/") == {"a/b": 1}

    def test_empty_dict(self):
        assert flatten_keys({}) == {}

    def test_non_dict_values_preserved(self):
        assert flatten_keys({"a": [1, 2], "b": {"c": 3}}) == {"a": [1, 2], "b.c": 3}
