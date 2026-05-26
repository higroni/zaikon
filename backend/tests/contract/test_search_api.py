"""Contract tests for search endpoints."""

from pathlib import Path


FIXTURE_DIR = Path(__file__).parents[1] / "regression" / "fixtures" / "corpus_folder_import"


def test_legal_unit_search_endpoint_after_import(client):
    corpus = client.post("/api/v1/corpora", json={"name": "Search corpus"}).json()[
        "corpus"
    ]
    client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(FIXTURE_DIR / "small_txt_corpus"),
        },
    )

    response = client.post(
        "/api/v1/search/legal-unit",
        json={"query": "Ministarstvo evidenciju", "top_k": 5},
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert results[0]["document_id"]
    assert results[0]["legal_unit_id"]
    assert "ministarstvo" in results[0]["metadata"]["matched_terms"]
