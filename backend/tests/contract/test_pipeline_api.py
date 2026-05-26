"""Contract tests for scaffold pipeline endpoint."""


def test_echo_pipeline_endpoint_contract(client):
    response = client.post("/api/v1/pipeline/echo", json={"message": "contract-ok"})

    assert response.status_code == 200
    body = response.json()
    assert body["chain_name"] == "EchoChain"
    assert body["status"] == "completed"
    assert body["artifacts"]["echo_result"]["payload"]["message"] == "contract-ok"

