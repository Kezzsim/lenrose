from __future__ import annotations

import pytest
from typesense.exceptions import ObjectNotFound, RequestForbidden

from lenrose.indexer.rebuild import recreate_collection


class _Collection:
    def __init__(self, delete_error: Exception | None = None) -> None:
        self.delete_error = delete_error
        self.deleted = False

    def delete(self) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted = True


class _Collections:
    def __init__(self, delete_error: Exception | None = None) -> None:
        self.collection = _Collection(delete_error)
        self.created = False

    def __getitem__(self, _name: str) -> _Collection:
        return self.collection

    def create(self, _schema: dict) -> None:
        self.created = True


class _Client:
    def __init__(self, delete_error: Exception | None = None) -> None:
        self.collections = _Collections(delete_error)


def test_recreate_collection_ignores_missing_collection() -> None:
    client = _Client(ObjectNotFound("not found"))

    recreate_collection(client, "idx", [])

    assert client.collections.created is True


def test_recreate_collection_does_not_hide_auth_errors() -> None:
    client = _Client(RequestForbidden("forbidden"))

    with pytest.raises(RequestForbidden):
        recreate_collection(client, "idx", [])

    assert client.collections.created is False
