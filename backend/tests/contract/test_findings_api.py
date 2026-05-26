"""Contract tests for finding endpoints."""


def test_finding_detail_and_review_decision_endpoints(client):
    create_response = client.post(
        "/api/v1/draft-reviews",
        json={
            "title": "Nacrt zakona o nalazima",
            "content_text": (
                "NACRT ZAKONA O NALAZIMA\n\n"
                "Clan 1.\n"
                "Ovaj nacrt upucuje na clan 99.\n"
            ),
        },
    )
    pipeline_run_id = create_response.json()["draft_review"]["pipeline_run_id"]
    run_response = client.post(f"/api/v1/draft-reviews/{pipeline_run_id}/run")
    finding_id = run_response.json()["findings"][0]["finding_id"]

    finding_response = client.get(f"/api/v1/findings/{finding_id}")

    assert finding_response.status_code == 200
    finding = finding_response.json()
    assert finding["finding_id"] == finding_id
    assert finding["status"] == "open"

    decision_response = client.patch(
        f"/api/v1/findings/{finding_id}/review-decision",
        json={"status": "accepted", "review_note": "Potvrdjeno u proveri."},
    )

    assert decision_response.status_code == 200
    updated = decision_response.json()["finding"]
    assert updated["finding_id"] == finding_id
    assert updated["status"] == "accepted"
    assert updated["review_note"] == "Potvrdjeno u proveri."
    assert updated["updated_at"] is not None

    repeated_get = client.get(f"/api/v1/findings/{finding_id}")

    assert repeated_get.status_code == 200
    assert repeated_get.json()["status"] == "accepted"
