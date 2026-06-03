"""Contract tests for slot-based assertion conflict evaluation."""


def _import_single_file_corpus(client, tmp_path, *, name: str, filename: str, text: str):
    corpus_dir = tmp_path / name
    corpus_dir.mkdir()
    (corpus_dir / filename).write_text(text, encoding="utf-8")
    corpus = client.post("/api/v1/corpora", json={"name": name}).json()["corpus"]
    response = client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(corpus_dir),
        },
    )
    assert response.status_code == 200
    return corpus


def test_slot_engine_flags_deadline_mismatch(client, tmp_path):
    corpus = _import_single_file_corpus(
        client,
        tmp_path,
        name="deadline-corpus",
        filename="zakon-rok.txt",
        text=(
            "Zakon o roku\n\n"
            "Clan 1.\n"
            "Nadlezni organ odlucuje u roku od 30 dana.\n"
        ),
    )
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa kracim rokom",
            "selected_corpus_id": corpus["corpus_id"],
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Nadlezni organ odlucuje u roku od 15 dana.\n"
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    findings = run_response.json()["findings"]
    deadline_findings = [
        finding for finding in findings if finding["finding_type"] == "deadline_mismatch"
    ]
    assert deadline_findings
    slot_diff = deadline_findings[0]["evidence"]["slot_diffs"][0]
    assert slot_diff["draft_value"] == "15 day"
    assert slot_diff["corpus_value"] == "30 day"
    trace_response = client.get(
        f"/api/v1/draft-reviews/{pipeline_run_id}/conflict-trace"
    )
    assert trace_response.status_code == 200
    assert trace_response.json()["candidate_count"] >= 1


def test_slot_engine_flags_wrong_competence_domain(client, tmp_path):
    corpus = _import_single_file_corpus(
        client,
        tmp_path,
        name="food-competence-corpus",
        filename="zakon-hrana.txt",
        text=(
            "Zakon o hrani\n\n"
            "Clan 1.\n"
            "Kontrolu hrane vrsi sanitarna inspekcija.\n"
        ),
    )
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt sa pogresnom nadleznoscu",
            "selected_corpus_id": corpus["corpus_id"],
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Kontrolu hrane vrsi inspekcija ministarstva nadleznog za gradjevinu.\n"
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    findings = run_response.json()["findings"]
    competence_findings = [
        finding for finding in findings if finding["finding_type"] == "competence_conflict"
    ]
    assert competence_findings
    slot_diff = competence_findings[0]["evidence"]["slot_diffs"][0]
    assert slot_diff["relation"] == "wrong_domain_for_object"
    assert slot_diff["draft_value"] == "construction_ministry"
    assert slot_diff["corpus_value"] == "health_ministry"
    candidates_response = client.get(
        f"/api/v1/draft-reviews/{pipeline_run_id}/conflict-candidates"
    )
    assert candidates_response.status_code == 200
    assert candidates_response.json()
