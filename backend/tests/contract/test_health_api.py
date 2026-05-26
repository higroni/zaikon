"""Contract tests for health endpoints."""


def test_health_endpoint_contract(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["module_name"] == "zaikon-api"
    assert body["status"] == "ok"
    assert "checked_at" in body


def test_modules_health_endpoint_contract(client):
    response = client.get("/api/v1/modules/health")

    assert response.status_code == 200
    modules = {item["module_name"] for item in response.json()}
    assert "corpus" in modules
    assert "llm" in modules
    assert "reports" in modules

