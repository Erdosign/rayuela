# Create a simple test file: tests/test_testclient.py
from fastapi.testclient import TestClient
from app.main import app

def test_testclient_basic():
    client = TestClient(app)
    response = client.get("/")
    # This should work even if it returns 404
    print(f"Status: {response.status_code}")
    assert response.status_code in [200, 404, 405]  # Any of these means it's working