"""Tests for result-list display field configuration."""

from lenrose.server.routes import search
from lenrose.state.models import KeySpec


def test_display_fields_defaults_to_uuid(monkeypatch):
    monkeypatch.setattr(search.db, "load_key_specs", lambda: [])

    assert search.display_fields() == {
        "default": "uuid",
        "options": [{"value": "uuid", "label": "UUID", "field": "uuid"}],
    }


def test_display_fields_exposes_selected_key(monkeypatch):
    specs = [
        KeySpec(dotted_key="start.plan_name", datatype="string", is_display=True),
        KeySpec(dotted_key="sample.name", datatype="string"),
    ]
    monkeypatch.setattr(search.db, "load_key_specs", lambda: specs)

    assert search.display_fields() == {
        "default": "start.plan_name",
        "options": [
            {"value": "uuid", "label": "UUID", "field": "uuid"},
            {
                "value": "start.plan_name",
                "label": "start.plan_name",
                "field": "plan_name",
            },
        ],
    }


def test_display_fields_uses_scoped_name_for_collisions(monkeypatch):
    specs = [
        KeySpec(dotted_key="sample.name", datatype="string", is_display=True),
        KeySpec(dotted_key="instrument.name", datatype="string"),
    ]
    monkeypatch.setattr(search.db, "load_key_specs", lambda: specs)

    options = search.display_fields()["options"]
    assert options[1] == {
        "value": "sample.name",
        "label": "sample.name",
        "field": "sample_name",
    }


def test_display_field_is_not_returned_as_facet(monkeypatch):
    specs = [
        KeySpec(
            dotted_key="sample.name",
            datatype="string",
            is_display=True,
            is_facet=True,
        ),
        KeySpec(dotted_key="sample.type", datatype="string", is_facet=True),
    ]
    monkeypatch.setattr(search.db, "load_key_specs", lambda: specs)

    assert search.display_fields()["options"][1] == {
        "value": "sample.name",
        "label": "sample.name",
        "field": "name",
    }
    assert search.facets()["facets"] == ["collection", "type"]
