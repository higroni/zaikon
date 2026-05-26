"""Contract tests for draft review endpoints."""

from pathlib import Path


FIXTURE_DIR = (
    Path(__file__).parents[1]
    / "regression"
    / "fixtures"
    / "corpus_folder_import"
    / "small_txt_corpus"
)


def test_draft_review_run_reports_missing_internal_reference(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt zakona o testu",
            "content_text": (
                "NACRT ZAKONA O TESTU\n\n"
                "Clan 1.\n"
                "Ovim zakonom upucuje se na clan 99.\n"
            ),
        },
    )

    assert create_response.status_code == 200
    draft_review = create_response.json()["draft_review"]
    pipeline_run_id = draft_review["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["draft_review"]["status"] == "completed"
    assert run_payload["draft_review"]["finding_count"] == 1
    assert run_payload["findings"][0]["finding_type"] == "reference_missing"
    assert run_payload["findings"][0]["risk_level"] == "high"

    findings_response = client.get(f"/api/v1/draft-reviews/{pipeline_run_id}/findings")

    assert findings_response.status_code == 200
    findings = findings_response.json()
    assert len(findings) == 1
    assert findings[0]["evidence"]["target_article_number"] == "99"


def test_draft_review_normalizes_cyrillic_before_reference_check(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "\u041d\u0430\u0446\u0440\u0442",
            "content_text": (
                "\u041d\u0410\u0426\u0420\u0422 \u0417\u0410\u041a\u041e\u041d\u0410\n\n"
                "\u0427\u043b\u0430\u043d 1.\n"
                "\u0423\u043f\u0443\u045b\u0443\u0458\u0435 \u0441\u0435 \u043d\u0430 "
                "\u0447\u043b\u0430\u043d 99.\n"
            ),
        },
    )

    assert create_response.status_code == 200
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    findings = run_response.json()["findings"]
    assert len(findings) == 1
    assert findings[0]["finding_type"] == "reference_missing"
    assert findings[0]["evidence"]["target_article_number"] == "99"


def test_draft_review_can_be_created_from_docx_file(client):
    create_response = client.post(
        "/api/v1/draft-reviews/from-file",
        json={"source_uri": str(FIXTURE_DIR / "pravilnik.docx")},
    )

    assert create_response.status_code == 200
    draft_review = create_response.json()["draft_review"]
    assert draft_review["title"] == "pravilnik"
    assert draft_review["metadata"]["input_type"] == "file"
    assert draft_review["metadata"]["file_type"] == "docx"

    detail_response = client.get(
        f"/api/v1/draft-reviews/{draft_review['pipeline_run_id']}"
    )

    assert detail_response.status_code == 200
    assert "Pravilnik" in detail_response.json()["content_text"]


def test_draft_review_can_be_created_and_run_from_pdf_file(client):
    create_response = client.post(
        "/api/v1/draft-reviews/from-file",
        json={"source_uri": str(FIXTURE_DIR / "uredba.pdf")},
    )

    assert create_response.status_code == 200
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["draft_review"]["status"] == "completed"
    assert payload["draft_review"]["metadata"]["input_type"] == "file"
    assert payload["draft_review"]["metadata"]["file_type"] == "pdf"
