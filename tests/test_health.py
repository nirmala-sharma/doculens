# TestClient simulates HTTP requests without needing a running server
from fastapi.testclient import TestClient
from app.main import app

# Create a fake client that hits our FastAPI app directly
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    # Must return HTTP 200 (success) — anything else means app is broken
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Doculens-api",
        "version": "0.1.0"
    }