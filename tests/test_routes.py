# tests/test_routes.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_routes():
    """List all registered routes to debug the 405 errors."""
    for route in app.routes:
        print(f"{route.methods} {route.path}")