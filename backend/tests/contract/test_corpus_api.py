"""Contract tests for corpus API endpoints."""

from pathlib import Path


FIXTURE_DIR = Path(__file__).parents[1] / "regression" / "fixtures" / "corpus_folder_import"


def test_create_corpus_and_import_folder_contract(client):
    create_response = client.post(
        "/api/v1/corpora",
        json={
            "name": "Regresioni korpus",
            "description": "Small TXT fixture",
            "language_code": "sr",
            "domain": "test",
        },
    )

    assert create_response.status_code == 200
    corpus = create_response.json()["corpus"]
    assert corpus["corpus_id"]
    assert corpus["language_code"] == "sr"

    import_response = client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(FIXTURE_DIR / "small_txt_corpus"),
        },
    )

    assert import_response.status_code == 200
    body = import_response.json()
    assert body["import_job"]["status"] == "completed"
    assert body["report"]["summary"] == {
        "total_files": 4,
        "supported_files": 3,
        "unsupported_files": 1,
        "extracted_documents": 3,
        "failed_files": 0,
        "document_types": {
            "law": 1,
            "regulation": 1,
            "rulebook": 1,
        },
        "stored_documents": 3,
    }
    assert body["report"]["source_files"][0]["source_uri"].startswith("file://")
    completed_source_files = [
        item
        for item in body["report"]["source_files"]
        if item["import_status"] == "completed"
    ]
    assert {item["document_type"] for item in completed_source_files} == {
        "law",
        "regulation",
        "rulebook",
    }
    assert all(
        item["document_type_confidence"] >= 0.55 for item in completed_source_files
    )
    assert "canonical_documents" in body["report"]["artifact_names"]
    assert set(body["report"]["index_reports"]) == {
        "keyword",
        "vector",
        "structure",
        "reference_graph",
    }


def test_import_report_endpoint_contract(client):
    corpus = client.post("/api/v1/corpora", json={"name": "Report corpus"}).json()[
        "corpus"
    ]
    import_body = client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(FIXTURE_DIR / "small_txt_corpus"),
        },
    ).json()

    report_response = client.get(
        f"/api/v1/import-jobs/{import_body['import_job']['import_job_id']}/report"
    )

    assert report_response.status_code == 200
    assert report_response.json()["report"]["status"] == "completed"
    assert report_response.json()["report"]["summary"]["extracted_documents"] == 3


def test_import_artifacts_endpoint_contract(client):
    corpus = client.post("/api/v1/corpora", json={"name": "Artifacts corpus"}).json()[
        "corpus"
    ]
    import_body = client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(FIXTURE_DIR / "small_txt_corpus"),
        },
    ).json()
    import_job_id = import_body["import_job"]["import_job_id"]

    artifacts_response = client.get(f"/api/v1/import-jobs/{import_job_id}/artifacts")

    assert artifacts_response.status_code == 200
    artifact_names = artifacts_response.json()
    assert "canonical_documents" in artifact_names
    assert "import_report" in artifact_names

    artifact_response = client.get(
        f"/api/v1/import-jobs/{import_job_id}/artifacts/canonical_documents"
    )

    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["name"] == "canonical_documents"
    assert artifact["payload"][0]["canonical_json"]["schema_version"] == "0.1"
