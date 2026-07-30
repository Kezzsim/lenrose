"""Integration tests against a live Typesense server (skipped if unavailable)."""

from lenrose.indexer.ingest import documents_from_container, import_documents
from lenrose.indexer.rebuild import recreate_collection
from lenrose.state.models import KeySpec


def _specs():
    return [
        KeySpec(dotted_key="start.plan_name", datatype="string", is_searchable=True),
        KeySpec(dotted_key="sample.name", datatype="string", is_facet=True),
    ]


def test_index_and_search_by_collection(typesense_client, typesense_settings, fake_container):
    index = typesense_settings.lenrose_index_name
    recreate_collection(typesense_client, index, _specs())

    docs = documents_from_container(fake_container, "bmm", _specs(), limit=10)
    imported = import_documents(typesense_client, index, docs)
    assert imported == 2

    result = typesense_client.collections[index].documents.search(
        {
            "q": "*",
            "query_by": "collection",
            "facet_by": "collection",
            "filter_by": "collection:=bmm",
        }
    )
    assert result["found"] == 2
    facet_fields = {f["field_name"] for f in result.get("facet_counts", [])}
    assert "collection" in facet_fields


def test_search_by_plan_name(typesense_client, typesense_settings, fake_container):
    index = typesense_settings.lenrose_index_name
    recreate_collection(typesense_client, index, _specs())
    docs = documents_from_container(fake_container, "bmm", _specs(), limit=10)
    import_documents(typesense_client, index, docs)

    result = typesense_client.collections[index].documents.search(
        {"q": "count", "query_by": "start__plan_name"}
    )
    assert result["found"] == 1
    assert result["hits"][0]["document"]["tiled_key"] == "bmm/scan_001"
