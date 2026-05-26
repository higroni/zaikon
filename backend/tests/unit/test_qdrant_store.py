"""Unit tests for the local Qdrant vector store adapter."""

from zaikon.modules.indexing.qdrant_store import QdrantVectorStore


def test_local_qdrant_store_round_trip(tmp_path):
    store = QdrantVectorStore(path=tmp_path / "qdrant_storage")
    collection_name = "test_legal_units"

    store.ensure_collection(collection_name, vector_size=3)
    store.upsert_vectors(
        collection_name=collection_name,
        vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        payloads=[
            {"legal_unit_id": "article-1", "content_text": "Clan 1"},
            {"legal_unit_id": "article-2", "content_text": "Clan 2"},
        ],
        ids=[1, 2],
    )

    results = store.search(collection_name, query_vector=[1.0, 0.0, 0.0], limit=1)

    assert len(results) == 1
    assert results[0]["payload"]["legal_unit_id"] == "article-1"
