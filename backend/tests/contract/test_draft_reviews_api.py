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


def test_draft_review_from_file_returns_400_for_missing_file(client, tmp_path):
    response = client.post(
        "/api/v1/draft-reviews/from-file",
        json={"source_uri": str(tmp_path / "missing.docx")},
    )

    assert response.status_code == 400
    assert "Draft file not found" in response.json()["detail"]


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


def test_draft_review_uses_selected_corpus_for_retrieval_artifact(client):
    corpus = client.post(
        "/api/v1/corpora", json={"name": "Draft retrieval corpus"}
    ).json()["corpus"]
    client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(FIXTURE_DIR),
        },
    )
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa retrieval kontekstom",
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Ministarstvo vodi evidenciju i upucuje na clan 99.\n"
            ),
            "selected_corpus_id": corpus["corpus_id"],
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["draft_review"]["metadata"]["retrieval_result_count"] > 0
    related_units = payload["findings"][0]["evidence"]["related_legal_units"]
    assert related_units
    assert {unit["corpus_id"] for unit in related_units} == {corpus["corpus_id"]}

    detail_response = client.get(f"/api/v1/draft-reviews/{pipeline_run_id}")

    assert detail_response.status_code == 200
    retrieval_results = detail_response.json()["artifacts"]["retrieval_results"]
    assert retrieval_results
    assert {result["corpus_id"] for result in retrieval_results} == {
        corpus["corpus_id"]
    }


def test_draft_review_flags_authorized_actor_conflict_from_selected_corpus(
    client, tmp_path
):
    corpus_dir = tmp_path / "authority"
    corpus_dir.mkdir()
    (corpus_dir / "zakon-o-sumama.txt").write_text(
        (
            "Zakon o sumama\n\n"
            "Clan 45.\n"
            "Obelezavanje drveca za secu vrsi ovlasceno preduzece u skladu "
            "sa zakonom i planom gazdovanja sumama.\n"
        ),
        encoding="utf-8",
    )
    corpus = client.post(
        "/api/v1/corpora", json={"name": "Authority conflict corpus"}
    ).json()["corpus"]
    client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(corpus_dir),
        },
    )
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa prosirenim ovlascenjem",
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Postupak se sprovodi u skladu sa clanom 2. Zakona o sumama. "
                "Obelezavanje drveca moze da radi svaki gradjanin.\n"
            ),
            "selected_corpus_id": corpus["corpus_id"],
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    findings = run_response.json()["findings"]
    authority_findings = [
        finding
        for finding in findings
        if finding["finding_type"] == "corpus_authority_conflict"
    ]
    assert authority_findings
    finding = authority_findings[0]
    assert finding["risk_level"] == "high"
    assert "svaki gradjanin" in finding["evidence"]["draft_quote"].lower()
    assert finding["evidence"]["corpus_conflicts"]
    assert "ovlasceno preduzece" in finding["evidence"]["corpus_conflicts"][0][
        "quote"
    ].lower()


def test_draft_review_resolves_cross_document_reference_from_selected_corpus(
    client, tmp_path
):
    corpus_dir = tmp_path / "cross"
    corpus_dir.mkdir()
    (corpus_dir / "zakon-o-sumama.txt").write_text(
        "Zakon o šumama\n\nČlan 2.\nŠume su dobro od opšteg interesa.",
        encoding="utf-8",
    )
    corpus = client.post(
        "/api/v1/corpora", json={"name": "Cross reference corpus"}
    ).json()["corpus"]
    client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(corpus_dir),
        },
    )
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa eksternom referencom",
            "content_text": (
                "NACRT\n\n"
                "Član 1.\n"
                "Postupak se sprovodi u skladu sa članom 2. Zakona o šumama."
            ),
            "selected_corpus_id": corpus["corpus_id"],
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    assert {
        finding["finding_type"] for finding in run_response.json()["findings"]
    } == set()
    detail_response = client.get(f"/api/v1/draft-reviews/{pipeline_run_id}")
    resolved_references = detail_response.json()["artifacts"]["resolved_references"][
        "resolved_references"
    ]
    assert resolved_references[0]["resolution_status"] == "resolved"
    assert "Zakon o šumama" in resolved_references[0]["resolution_note"]


def test_draft_review_reports_definition_conflicts(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa definicijama",
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Ministarstvo nadlezno za sume (u daljem tekstu: Ministarstvo).\n\n"
                "Clan 2.\n"
                "Ministarstvo nadlezno za finansije (u daljem tekstu: Ministarstvo).\n"
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    finding_types = {
        finding["finding_type"] for finding in run_response.json()["findings"]
    }
    assert "definition_conflict" in finding_types


def test_draft_review_runs_terminology_and_temporal_checkers(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa dodatnim proverama",
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Nadlezni organ vodi evidenciju od 31. februar 2026."
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    finding_types = {
        finding["finding_type"] for finding in run_response.json()["findings"]
    }
    assert "terminology_inconsistent" in finding_types
    assert "temporal_validity_issue" in finding_types


def test_draft_review_runs_advanced_checker_skeletons(client):
    repeated = "Organ vodi evidenciju o korisnicima sredstava i merama zastite."
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa naprednim proverama",
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Organ mora da postupi, ali ne sme da izda odobrenje.\n\n"
                f"{repeated}\n\n"
                "Clan 2.\n"
                f"{repeated}\n\n"
                "Danom stupanja na snagu ovog zakona prestaje da vazi raniji pravilnik."
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    finding_types = {
        finding["finding_type"] for finding in run_response.json()["findings"]
    }
    assert "possible_norm_conflict" in finding_types
    assert "possible_overlap" in finding_types
    assert "reference_stale" in finding_types


def test_draft_review_can_export_akoma_ntoso_after_run(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt za Akoma",
            "content_text": "NACRT\n\nClan 1.\nOvim nacrtom uredjuje se primer.",
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]
    client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    response = client.get(f"/api/v1/draft-reviews/{pipeline_run_id}/akoma-ntoso")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<akomaNtoso" in response.text
    assert "<FRBRlanguage language=\"srp\"" in response.text


def test_draft_review_artifact_endpoints_after_run(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa artefaktima",
            "content_text": "NACRT\n\nClan 1.\nOvim nacrtom uredjuje se primer.",
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]
    client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    list_response = client.get(f"/api/v1/draft-reviews/{pipeline_run_id}/artifacts")

    assert list_response.status_code == 200
    artifact_names = list_response.json()
    assert "canonical_document" in artifact_names
    assert "parsed_document" in artifact_names

    artifact_response = client.get(
        f"/api/v1/draft-reviews/{pipeline_run_id}/artifacts/canonical_document"
    )

    assert artifact_response.status_code == 200
    assert artifact_response.json()["canonical_json"]["schema_version"] == "0.1"
