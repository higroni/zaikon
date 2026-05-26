"""Unit tests for SQLite document storage."""

from zaikon.modules.storage.sqlite_store import SQLiteDocumentStore


def test_sqlite_document_store_round_trip(tmp_path):
    store = SQLiteDocumentStore(tmp_path / "zaikon.db")
    record = {
        "document_id": "doc-1",
        "corpus_id": "corpus-1",
        "source_uri": "file:///tmp/zakon.txt",
        "filename": "zakon.txt",
        "document_type": "law",
        "title": "Zakon",
        "publication_metadata": {"official_gazette_numbers": ["30"]},
    }
    canonical_json = {
        "schema_version": "0.1",
        "legal_units": [{"legal_unit_id": "unit-1"}],
    }

    store.upsert_document(record, canonical_json)

    loaded = store.get_document("doc-1")
    assert loaded is not None
    assert loaded["filename"] == "zakon.txt"
    assert loaded["canonical_json"] == canonical_json
    assert loaded["publication_metadata"]["official_gazette_numbers"] == ["30"]
    assert [item["document_id"] for item in store.list_documents("corpus-1")] == [
        "doc-1"
    ]
