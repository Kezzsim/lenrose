"""Tests for the consolidated search configuration endpoint."""

from lenrose.server.routes import search
from lenrose.state.models import KeySpec


def _patch_specs(monkeypatch, specs):
    monkeypatch.setattr(search.db, "load_key_specs", lambda: specs)


def _patch_key(monkeypatch):
    monkeypatch.setattr(
        "lenrose.server.routes.search.get_scoped_search_key",
        lambda settings=None: "scoped-key",
    )


def test_display_fields_default_to_uuid(monkeypatch):
    _patch_specs(monkeypatch, [])

    options, default = search._display_fields([])
    assert default == "uuid"
    assert options == [{"value": "uuid", "label": "UUID", "field": "uuid"}]


def test_display_fields_exposes_selected_key(monkeypatch):
    specs = [
        KeySpec(dotted_key="start.plan_name", datatype="string", is_display=True),
        KeySpec(dotted_key="sample.name", datatype="string"),
    ]
    options, default = search._display_fields(specs)
    assert default == "start.plan_name"
    assert options == [
        {"value": "uuid", "label": "UUID", "field": "uuid"},
        {"value": "start.plan_name", "label": "start.plan_name", "field": "plan_name"},
    ]


def test_display_fields_scoped_name_for_collisions():
    specs = [
        KeySpec(dotted_key="sample.name", datatype="string", is_display=True),
        KeySpec(dotted_key="instrument.name", datatype="string"),
    ]
    options, _ = search._display_fields(specs)
    assert options[1] == {
        "value": "sample.name",
        "label": "sample.name",
        "field": "sample_name",
    }


def test_display_field_not_returned_as_facet():
    specs = [
        KeySpec(
            dotted_key="sample.name",
            datatype="string",
            is_display=True,
            is_facet=True,
        ),
        KeySpec(dotted_key="sample.type", datatype="string", is_facet=True),
    ]
    options, _ = search._display_fields(specs)
    assert options[1] == {"value": "sample.name", "label": "sample.name", "field": "name"}
    assert search._facet_fields(specs) == ["collection", "type"]


def test_search_config_shape(monkeypatch):
    specs = [
        KeySpec(
            dotted_key="start.plan_name",
            datatype="string",
            is_display=True,
            is_searchable=True,
            is_index=True,
        ),
        KeySpec(dotted_key="sample.temperature", datatype="float", is_facet=True),
    ]
    _patch_specs(monkeypatch, specs)
    _patch_key(monkeypatch)

    cfg = search.search_config()

    assert cfg["typesense"]["apiKey"] == "scoped-key"
    assert "host" in cfg["typesense"]
    assert cfg["collection"]
    assert "temperature" in cfg["facets"]
    assert cfg["facetTypes"]["temperature"] == "float"
    assert cfg["defaultDisplay"] == "start.plan_name"
    assert "plan_name" in cfg["queryBy"]
    assert "configured" in cfg["tiled"]
    assert cfg["tiled"]["method"] in (None, "anonymous", "api_key")
    # Public Tiled API URL is exposed so the browser can load data directly.
    assert "apiUrl" in cfg["tiled"]
