"""Tests for schema building and document construction."""

from lenrose.indexer.ingest import (
    build_document,
    documents_from_container,
    make_doc_id,
    normalize_collection,
)
from lenrose.schema.builder import build_schema, system_key_specs
from lenrose.state.models import KeySpec


def test_schema_always_has_system_fields():
    schema = build_schema("idx", [])
    names = {f["name"] for f in schema["fields"]}
    assert {"uuid", "collection", "tiled_key"} <= names


def test_collection_is_faceted_by_default():
    schema = build_schema("idx", [])
    collection = next(f for f in schema["fields"] if f["name"] == "collection")
    assert collection["facet"] is True


def test_user_keys_are_sanitized_and_added():
    specs = [KeySpec(dotted_key="start.plan_name", datatype="string", is_facet=True)]
    schema = build_schema("idx", specs)
    field = next(f for f in schema["fields"] if f["name"] == "start__plan_name")
    assert field["type"] == "string"
    assert field["facet"] is True


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
    doc = build_document(
        uuid="abc",
        collection="bmm",
        metadata={"start": {"plan_name": "count"}},
        selected_keys={"start.plan_name"},
        structure_family="array",
        specs=["BlueskyRun"],
    )
    assert doc["uuid"] == "abc"
    assert doc["collection"] == "bmm"
    assert doc["tiled_key"] == "bmm/abc"
    assert doc["id"] == "bmm/abc"
    assert doc["start__plan_name"] == "count"
    assert doc["structure_family"] == "array"
    assert doc["specs"] == ["BlueskyRun"]


def test_build_document_excludes_unselected_keys():
    doc = build_document(
        uuid="abc",
        collection="bmm",
        metadata={"start": {"plan_name": "count", "secret": "x"}},
        selected_keys={"start.plan_name"},
    )
    assert "start__secret" not in doc


def test_documents_from_container(fake_container):
    specs = [
        KeySpec(dotted_key="start.plan_name", datatype="string"),
        KeySpec(dotted_key="sample.name", datatype="string"),
    ]
    docs = documents_from_container(fake_container, "bmm", specs, limit=10)
    assert len(docs) == 2
    assert all(d["collection"] == "bmm" for d in docs)
    assert all(d["tiled_key"].startswith("bmm/") for d in docs)
    assert {d["start__plan_name"] for d in docs} == {"count", "scan"}


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
    a = build_document(uuid="u1", collection="pokemon", metadata={}, selected_keys=set())
    b = build_document(uuid="u1", collection="/pokemon/", metadata={}, selected_keys=set())
    assert a["id"] == b["id"]
    assert a["collection"] == b["collection"] == "pokemon"
    assert a["tiled_key"] == b["tiled_key"] == "pokemon/u1"
