"""Contract tests for report endpoints."""

from pathlib import Path


def test_generate_and_download_markdown_report(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt za izvestaj",
            "content_text": (
                "NACRT ZAKONA O IZVESTAJU\n\n"
                "Clan 1.\n"
                "Ovaj nacrt upucuje na clan 99.\n"
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]
    client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    report_response = client.post(
        "/api/v1/reports",
        json={"pipeline_run_id": pipeline_run_id, "report_format": "markdown"},
    )

    assert report_response.status_code == 200
    report = report_response.json()["report"]
    assert report["pipeline_run_id"] == pipeline_run_id
    assert report["finding_count"] == 1
    assert "reference_missing" in report["content_text"]

    get_response = client.get(f"/api/v1/reports/{report['report_id']}")

    assert get_response.status_code == 200
    assert get_response.json()["report_id"] == report["report_id"]

    list_response = client.get("/api/v1/reports")

    assert list_response.status_code == 200
    assert any(item["report_id"] == report["report_id"] for item in list_response.json())

    download_response = client.get(f"/api/v1/reports/{report['report_id']}/download")

    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("text/markdown")
    assert "Izvestaj - Nacrt za izvestaj" in download_response.text


def test_generate_and_download_docx_report(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt za Word izvestaj",
            "content_text": (
                "NACRT ZAKONA O WORD IZVESTAJU\n\n"
                "Clan 1.\n"
                "Ovaj nacrt upucuje na clan 99.\n"
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]
    client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    report_response = client.post(
        "/api/v1/reports",
        json={"pipeline_run_id": pipeline_run_id, "report_format": "docx"},
    )

    assert report_response.status_code == 200
    report = report_response.json()["report"]
    assert report["report_format"] == "docx"
    assert report["metadata"]["download_path"].endswith(".docx")

    download_response = client.get(f"/api/v1/reports/{report['report_id']}/download")

    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert download_response.content[:2] == b"PK"


def test_generate_and_download_pdf_report(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt za PDF izvestaj",
            "content_text": (
                "NACRT ZAKONA O PDF IZVESTAJU\n\n"
                "Clan 1.\n"
                "Ovaj nacrt upucuje na clan 99.\n"
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]
    client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    report_response = client.post(
        "/api/v1/reports",
        json={"pipeline_run_id": pipeline_run_id, "report_format": "pdf"},
    )

    assert report_response.status_code == 200
    report = report_response.json()["report"]
    assert report["report_format"] == "pdf"
    assert report["metadata"]["download_path"].endswith(".pdf")

    download_response = client.get(f"/api/v1/reports/{report['report_id']}/download")

    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("application/pdf")
    assert download_response.content[:4] == b"%PDF"


def test_report_includes_related_legal_units_from_finding_evidence(client):
    corpus = client.post(
        "/api/v1/corpora", json={"name": "Report evidence corpus"}
    ).json()["corpus"]
    fixture_dir = (
        Path(__file__).parents[1]
        / "regression"
        / "fixtures"
        / "corpus_folder_import"
        / "small_txt_corpus"
    )
    client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(fixture_dir),
        },
    )
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa dokazima",
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Ministarstvo vodi evidenciju i upucuje na clan 99.\n"
            ),
            "selected_corpus_id": corpus["corpus_id"],
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]
    client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    report_response = client.post(
        "/api/v1/reports",
        json={"pipeline_run_id": pipeline_run_id, "report_format": "markdown"},
    )

    assert report_response.status_code == 200
    content_text = report_response.json()["report"]["content_text"]
    assert "Povezane pravne jedinice:" in content_text
    assert "score:" in content_text
    assert "Citat:" in content_text
