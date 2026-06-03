"""Contract tests for ontology and normative assertion extraction."""


def test_ontology_endpoint_exposes_base_serbian_terms(client):
    response = client.get("/api/v1/ontology")

    assert response.status_code == 200
    ontology = response.json()["ontology"]
    assert "any_person" in ontology["actors"]
    assert "construction_ministry" in ontology["actors"]
    assert "food" in ontology["objects"]
    assert "inspect" in ontology["actions"]


def test_draft_review_run_stores_normative_assertions(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt nadleznost i rok",
            "content_text": (
                "NACRT\n\n"
                "Clan 1.\n"
                "Kontrolu hrane vrsi inspekcija ministarstva nadleznog za gradjevinu. "
                "Organ odlucuje u roku od 15 dana.\n"
            ),
        },
    )
    assert create_response.status_code == 200
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]

    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")

    assert run_response.status_code == 200
    assertions_response = client.get(
        f"/api/v1/draft-reviews/{pipeline_run_id}/assertions"
    )
    assert assertions_response.status_code == 200
    assertions = assertions_response.json()
    assert assertions
    competence = next(
        item for item in assertions if item["assertion_type"] == "competence"
    )
    deadline = next(item for item in assertions if item["deadline"] is not None)
    assert competence["actor"]["canonical"] == "construction_ministry"
    assert competence["action"]["canonical"] == "inspect"
    assert competence["object"]["canonical"] == "food"
    assert deadline["deadline"]["value"] == 15


def test_corpus_import_writes_normative_assertion_artifact(client, tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "rok.txt").write_text(
        (
            "Zakon o roku\n\n"
            "Clan 1.\n"
            "Nadlezni organ odlucuje u roku od 30 dana.\n"
        ),
        encoding="utf-8",
    )
    corpus = client.post("/api/v1/corpora", json={"name": "Assertion corpus"}).json()[
        "corpus"
    ]
    import_response = client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(corpus_dir),
        },
    )

    assert import_response.status_code == 200
    import_job_id = import_response.json()["import_job"]["import_job_id"]
    artifact_names = client.get(
        f"/api/v1/import-jobs/{import_job_id}/artifacts"
    ).json()
    assert "normative_assertions" in artifact_names

    artifact_response = client.get(
        f"/api/v1/import-jobs/{import_job_id}/artifacts/normative_assertions"
    )
    assert artifact_response.status_code == 200
    payload = artifact_response.json()["payload"]
    assert payload[0]["assertions"][0]["deadline"]["value"] == 30
