from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Staff Management System!"
    assert data["version"] == "1.0.0"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_api_info():
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Staff Management System"
    assert data["version"] == "1.0.0"
    assert "suppliers" in data["endpoints"]
    assert "items" in data["endpoints"]
    assert "packaging_types" in data["endpoints"]
    assert "overhead_cost_types" in data["endpoints"]
    assert "supply_expenses" in data["endpoints"]

def test_docs_available():
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200

def test_redoc_available():
    """Test that ReDoc documentation is available."""
    response = client.get("/redoc")
    assert response.status_code == 200

def test_setup_endpoint():
    """Test the setup endpoint."""
    response = client.post("/setup")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "setup" in response.json()["message"].lower()
