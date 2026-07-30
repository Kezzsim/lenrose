"""Tests for container introspection using fake Tiled nodes."""

from lenrose.tiled_client.introspect import introspect_container, list_containers


class _Root:
    def __init__(self, containers):
        self._containers = containers

    def keys(self):
        return list(self._containers.keys())

    def __getitem__(self, key):
        return self._containers[key]


def test_introspect_discovers_nested_keys(fake_container):
    root = _Root({"bmm": fake_container})
    result = introspect_container(root, "bmm", limit=10)
    keys = {k.dotted_key for k in result.as_key_list()}
    assert "start.plan_name" in keys
    assert "start.num_points" in keys
    assert "start.detectors" in keys
    assert "sample.name" in keys
    assert result.scanned == 2


def test_introspect_types(fake_container):
    root = _Root({"bmm": fake_container})
    result = introspect_container(root, "bmm", limit=10)
    types = {k.dotted_key: k.datatype for k in result.as_key_list()}
    assert types["start.num_points"] == "int64"
    assert types["start.plan_name"] == "string"
    assert types["start.detectors"] == "string[]"


def test_list_containers(fake_container):
    root = _Root({"bmm": fake_container})
    infos = list_containers(root)
    assert any(i.path == "bmm" for i in infos)
