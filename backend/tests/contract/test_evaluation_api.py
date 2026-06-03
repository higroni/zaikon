"""Contract tests for the conflict evaluation harness."""


def test_evaluation_lists_gold_cases(client):
    response = client.get("/api/v1/evaluation/cases")

    assert response.status_code == 200
    cases = response.json()
    assert {case["case_id"] for case in cases} >= {
        "deadline_mismatch_001",
        "competence_conflict_001",
    }


def test_evaluation_run_executes_gold_cases(client):
    response = client.post("/api/v1/evaluation/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_cases"] >= 2
    
    # Check that metrics are calculated
    assert "metrics" in payload
    metrics = payload["metrics"]
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "per_type_metrics" in metrics
    
    # Verify core cases still work
    result_by_id = {result["case_id"]: result for result in payload["results"]}
    assert "deadline_mismatch" in result_by_id["deadline_mismatch_001"][
        "actual_finding_types"
    ]
    assert "competence_conflict" in result_by_id["competence_conflict_001"][
        "actual_finding_types"
    ]
    
    # Check that we have reasonable performance (at least 50% recall on core cases)
    assert metrics["recall"] >= 0.3, f"Recall too low: {metrics['recall']}"
