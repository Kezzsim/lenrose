"""Tests for schema building and document construction."""

import json
import enum

from lenrose.indexer.ingest import (
    build_document,
    documents_from_container,
    make_doc_id,
    normalize_collection,
    selected_field_names,
)
from lenrose.schema.builder import build_schema, system_key_specs
from lenrose.state.models import KeySpec


class _StructureFamily(enum.Enum):
    """Mimics Tiled's StructureFamily enum: str() -> 'StructureFamily.container'
    while .value -> 'container'."""

    container = "container"
    array = "array"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"StructureFamily.{self.name}"


def test_documents_store_clean_structure_family_from_enum(fake_container):
    # Give one record a real-enum-like structure_family.
    node = fake_container.children["scan_001"]
    node.structure_family = _StructureFamily.container

    docs = documents_from_container(fake_container, "bmm", [])
    by_id = {d["uuid"]: d for d in docs}

    assert by_id["scan_001"]["structure_family"] == "container"
    assert "StructureFamily" not in by_id["scan_001"]["structure_family"]


def test_schema_always_has_system_fields():
    schema = build_schema("idx", [])
    names = {f["name"] for f in schema["fields"]}
    assert {"uuid", "collection", "tiled_key"} <= names


def test_collection_is_faceted_by_default():
    schema = build_schema("idx", [])
    collection = next(f for f in schema["fields"] if f["name"] == "collection")
    assert collection["facet"] is True


def test_user_keys_use_leaf_field_names():
    specs = [KeySpec(dotted_key="start.plan_name", datatype="string", is_facet=True)]
    schema = build_schema("idx", specs)
    field = next(f for f in schema["fields"] if f["name"] == "plan_name")
    assert field["type"] == "string"
    assert field["facet"] is True


def test_display_field_is_never_schema_facet():
    specs = [
        KeySpec(
            dotted_key="sample.name",
            datatype="string",
            is_facet=True,
            is_display=True,
        )
    ]
    schema = build_schema("idx", specs)
    field = next(f for f in schema["fields"] if f["name"] == "name")
    assert field["facet"] is False


def test_unique_leaf_uses_bare_leaf_name():
    specs = [
        KeySpec(dotted_key="bmm.detectors.pilatus100k.size", datatype="int64"),
    ]
    schema = build_schema("idx", specs)
    names = {f["name"] for f in schema["fields"]}
    assert "size" in names


def test_colliding_leaves_are_path_scoped_even_when_same_type():
    # start.time and stop.time can both appear in one record; scoping each to
    # its full path prevents one silently overwriting the other.
    specs = [
        KeySpec(dotted_key="start.time", datatype="float"),
        KeySpec(dotted_key="stop.time", datatype="float"),
    ]
    schema = build_schema("idx", specs)
    names = {f["name"] for f in schema["fields"]}
    assert "start_time" in names
    assert "stop_time" in names
    assert "time" not in names


def test_colliding_leaves_deep_paths_stay_distinct():
    specs = [
        KeySpec(dotted_key="start.XDI.Beamline.name", datatype="string"),
        KeySpec(dotted_key="start.XDI.Facility.name", datatype="string"),
    ]
    schema = build_schema("idx", specs)
    names = {f["name"] for f in schema["fields"]}
    assert "start_XDI_Beamline_name" in names
    assert "start_XDI_Facility_name" in names
    assert "name" not in names


def test_user_cannot_clobber_system_field():
    specs = [KeySpec(dotted_key="collection", datatype="string")]
    schema = build_schema("idx", specs)
    collection_fields = [f for f in schema["fields"] if f["name"] == "collection"]
    assert len(collection_fields) == 1  # only the system one


def test_system_key_specs_marks_collection_facet():
    specs = system_key_specs()
    collection = next(s for s in specs if s.dotted_key == "collection")
    assert collection.is_facet is True
    assert collection.is_system is True


def test_build_document_stores_collection_and_tiled_key():
    field_names = selected_field_names(
        [KeySpec(dotted_key="start.plan_name", datatype="string")]
    )
    doc = build_document(
        uuid="abc",
        collection="bmm",
        metadata={"start": {"plan_name": "count"}},
        field_names=field_names,
        structure_family="array",
        specs=["BlueskyRun"],
    )
    assert doc["uuid"] == "abc"
    assert doc["collection"] == "bmm"
    assert doc["tiled_key"] == "bmm/abc"
    assert doc["id"] == "bmm/abc"
    assert doc["plan_name"] == "count"
    assert json.loads(doc["_parents"])["plan_name"] == "start"
    assert doc["structure_family"] == "array"
    assert doc["specs"] == ["BlueskyRun"]


def test_build_document_excludes_unselected_keys():
    field_names = selected_field_names(
        [KeySpec(dotted_key="start.plan_name", datatype="string")]
    )
    doc = build_document(
        uuid="abc",
        collection="bmm",
        metadata={"start": {"plan_name": "count", "secret": "x"}},
        field_names=field_names,
    )
    assert "secret" not in doc


def test_build_document_coerces_nested_list_to_json_string():
    # A nested list (e.g. hints.dimensions) declared as a scalar 'string' field
    # must be JSON-serialised so Typesense does not reject the document.
    spec = KeySpec(dotted_key="start.hints.dimensions", datatype="string")
    field_names = selected_field_names([spec])
    field_types = {spec.dotted_key: spec.datatype}
    doc = build_document(
        uuid="u1",
        collection="bmm",
        metadata={"start": {"hints": {"dimensions": [[["e"], "primary"]]}}},
        field_names=field_names,
        field_types=field_types,
    )
    assert doc["dimensions"] == json.dumps(
        [[["e"], "primary"]], default=str, sort_keys=True
    )


def test_documents_from_container(fake_container):
    specs = [
        KeySpec(dotted_key="start.plan_name", datatype="string"),
        KeySpec(dotted_key="sample.name", datatype="string"),
    ]
    docs = documents_from_container(fake_container, "bmm", specs, limit=10)
    assert len(docs) == 2
    assert all(d["collection"] == "bmm" for d in docs)
    assert all(d["tiled_key"].startswith("bmm/") for d in docs)
    assert {d["plan_name"] for d in docs} == {"count", "scan"}


def test_normalize_collection_canonicalizes_variants():
    # All of these refer to the same container and must collapse to one string.
    assert normalize_collection("pokemon") == "pokemon"
    assert normalize_collection("pokemon/") == "pokemon"
    assert normalize_collection("/pokemon") == "pokemon"
    assert normalize_collection("  pokemon  ") == "pokemon"
    assert normalize_collection("a//b/") == "a/b"
    assert normalize_collection("") == ""
    assert normalize_collection(None) == ""


def test_make_doc_id_is_stable_across_path_variants():
    # The batch path ("pokemon") and a webhook path join ("/pokemon") must yield
    # the same document id so the object is not duplicated.
    assert make_doc_id("pokemon", "u1") == make_doc_id("/pokemon/", "u1")
    assert make_doc_id("pokemon", "u1") == "pokemon/u1"
    # Root container: no spurious leading slash.
    assert make_doc_id("", "u1") == "u1"


def test_build_document_dedups_root_and_slashed_collection():
    a = build_document(uuid="u1", collection="pokemon", metadata={}, field_names={})
    b = build_document(uuid="u1", collection="/pokemon/", metadata={}, field_names={})
    assert a["id"] == b["id"]
    assert a["collection"] == b["collection"] == "pokemon"
    assert a["tiled_key"] == b["tiled_key"] == "pokemon/u1"
