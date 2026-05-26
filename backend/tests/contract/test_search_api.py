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


def test_search_can_be_limited_to_corpus(client, tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    (first_dir / "zakon-a.txt").write_text(
        "Zakon A\n\nClan 1.\nJedinstvenipojam pripada prvom korpusu.",
        encoding="utf-8",
    )
    (second_dir / "zakon-b.txt").write_text(
        "Zakon B\n\nClan 1.\nDrugipojam pripada drugom korpusu.",
        encoding="utf-8",
    )
    first_corpus = client.post(
        "/api/v1/corpora", json={"name": "First search corpus"}
    ).json()["corpus"]
    second_corpus = client.post(
        "/api/v1/corpora", json={"name": "Second search corpus"}
    ).json()["corpus"]
    client.post(
        f"/api/v1/corpora/{first_corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": first_corpus["corpus_id"],
            "folder_uri": str(first_dir),
        },
    )
    client.post(
        f"/api/v1/corpora/{second_corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": second_corpus["corpus_id"],
            "folder_uri": str(second_dir),
        },
    )

    filtered_response = client.post(
        "/api/v1/search/hybrid",
        json={
            "query": "jedinstvenipojam",
            "top_k": 5,
            "corpus_id": second_corpus["corpus_id"],
        },
    )
    matching_response = client.post(
        "/api/v1/search/hybrid",
        json={
            "query": "jedinstvenipojam",
            "top_k": 5,
            "corpus_id": first_corpus["corpus_id"],
        },
    )

    assert filtered_response.status_code == 200
    assert filtered_response.json()["results"] == []
    assert matching_response.status_code == 200
    results = matching_response.json()["results"]
    assert results
    assert {result["corpus_id"] for result in results} == {first_corpus["corpus_id"]}
