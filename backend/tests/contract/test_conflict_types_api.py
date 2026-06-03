"""Contract tests for the comprehensive conflict type registry."""


def test_conflict_registry_exposes_comprehensive_categories(client):
    response = client.get("/api/v1/conflicts/types")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 120
    finding_types = {
        conflict_type["finding_type"]
        for conflict_type in payload["conflict_types"]
    }
    assert "authority_scope_conflict" in finding_types
    assert "deadline_mismatch" in finding_types
    assert "competence_conflict" in finding_types
    assert "wrong_inspection_authority" in finding_types
    assert "eu_alignment_table_missing" in finding_types
    assert "public_consultation_duration_short" in finding_types


def test_conflict_registry_can_filter_by_category(client):
    response = client.get("/api/v1/conflicts/types?category=eu_alignment")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 10
    assert {
        conflict_type["category"]
        for conflict_type in payload["conflict_types"]
    } == {"eu_alignment"}


def test_conflict_registry_returns_single_type(client):
    response = client.get("/api/v1/conflicts/types/competence_conflict")

    assert response.status_code == 200
    payload = response.json()
    assert payload["finding_type"] == "competence_conflict"
    assert payload["category"] == "competence_and_institutions"
    assert "actor" in payload["required_slots"]


def test_conflict_registry_reload_reads_rule_pack(client):
    response = client.post("/api/v1/conflicts/reload")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 120
    assert "procedural_compliance" in payload["categories"]
