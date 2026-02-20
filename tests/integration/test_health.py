"""Integration test for the health endpoint."""

from fastapi.testclient import TestClient

from sentinelcx.api.app import create_app


def test_health_endpoint():
    """Verify the health endpoint returns OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sentinelCX"
