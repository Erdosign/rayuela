# tests/test_routes.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_routes():
    """List all registered routes to debug the 405 errors."""
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            # Regular route with methods and path
            print(f"{route.methods} {route.path}")
        elif hasattr(route, 'routes'):
            # Mount object - contains sub-routes
            for sub_route in route.routes:
                if hasattr(sub_route, 'methods') and hasattr(sub_route, 'path'):
                    full_path = route.path + sub_route.path
                    print(f"{sub_route.methods} {full_path}")
        else:
            # Other types of routes
            print(f"Route type: {type(route).__name__}")