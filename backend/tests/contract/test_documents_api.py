"""Contract tests for document catalog endpoints."""

from pathlib import Path


FIXTURE_DIR = Path(__file__).parents[1] / "regression" / "fixtures" / "corpus_folder_import"


def test_document_catalog_endpoints_after_import(client):
    corpus = client.post("/api/v1/corpora", json={"name": "Document API corpus"}).json()[
        "corpus"
    ]
    client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(FIXTURE_DIR / "small_txt_corpus"),
        },
    )

    documents_response = client.get("/api/v1/documents")

    assert documents_response.status_code == 200
    documents = documents_response.json()
    imported_documents = [
        document for document in documents if document["filename"] == "zakon.txt"
    ]
    assert imported_documents
    document_id = imported_documents[-1]["document_id"]

    document_response = client.get(f"/api/v1/documents/{document_id}")

    assert document_response.status_code == 200
    document = document_response.json()
    assert document["filename"] == "zakon.txt"
    assert document["canonical_json"]["schema_version"] == "0.1"
    legal_unit_id = document["canonical_json"]["legal_units"][0]["legal_unit_id"]

    legal_unit_response = client.get(f"/api/v1/legal-units/{legal_unit_id}")

    assert legal_unit_response.status_code == 200
    legal_unit = legal_unit_response.json()
    assert legal_unit["document_id"] == document_id
    assert legal_unit["legal_unit_id"] == legal_unit_id

    akoma_response = client.get(f"/api/v1/documents/{document_id}/akoma-ntoso")

    assert akoma_response.status_code == 200
    assert akoma_response.headers["content-type"].startswith("application/xml")
    assert "<akomaNtoso" in akoma_response.text
    assert "<FRBRlanguage language=\"srp\"" in akoma_response.text
