"""Tests for metadata flattening and type inference."""

from lenrose.tiled_client.introspect import flatten, infer_type, _reconcile


def test_flatten_nested():
    md = {"start": {"plan_name": "count", "num": 5}, "top": 1}
    flat = flatten(md)
    assert flat == {"start.plan_name": "count", "start.num": 5, "top": 1}


def test_flatten_keeps_scalar_lists():
    md = {"start": {"detectors": ["a", "b"]}}
    assert flatten(md) == {"start.detectors": ["a", "b"]}


def test_infer_type_scalars():
    assert infer_type(True) == "bool"
    assert infer_type(5) == "int64"
    assert infer_type(1.2) == "float"
    assert infer_type("x") == "string"


def test_infer_type_bool_before_int():
    # bool is a subclass of int; must be checked first
    assert infer_type(False) == "bool"


def test_infer_type_lists():
    assert infer_type([1, 2]) == "int64[]"
    assert infer_type(["a"]) == "string[]"
    # Empty and non-scalar/mixed lists cannot be a typed array -> stringify.
    assert infer_type([]) == "string"


def test_infer_type_nested_and_mixed_lists_stringify():
    # Bluesky hints.dimensions: list of lists -> not a scalar array.
    assert infer_type([[["dcm_energy"], "primary"]]) == "string"
    assert infer_type([1, "a"]) == "string"
    assert infer_type([{"a": 1}]) == "string"


def test_reconcile_conflicts():
    assert _reconcile("int64", "float") == "float"
    assert _reconcile("int64", "string") == "string"
    assert _reconcile("int64", "int64[]") == "string[]"
    assert _reconcile("string", "string") == "string"
