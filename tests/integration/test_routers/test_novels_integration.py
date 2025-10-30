import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch
from app.main import app
from app.crud.novel_crud import ProjectCRUD

# Use direct TestClient instantiation
client = TestClient(app)

class TestNovelsRouterIntegration:
    """Integration tests for novels API endpoints with actual database operations."""
    
    def test_create_and_retrieve_project(self, db_session):
        """Test full project lifecycle: create, retrieve, update, delete."""
        # Create project
        project_data = {
            "title": "Integration Test Novel",
            "description": "A novel for integration testing",
            "author": "Test Author",
            "genre": "Mystery"
        }
        
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # Create project
            response = client.post("/projects/", json=project_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_project = response.json()
            project_id = created_project["id"]
            
            # Retrieve project
            response = client.get(f"/projects/{project_id}")
            assert response.status_code == status.HTTP_200_OK
            
            # Update project
            update_data = {"title": "Updated Integration Test Novel"}
            response = client.put(f"/projects/{project_id}", json=update_data)
            assert response.status_code == status.HTTP_200_OK
            updated_project = response.json()
            assert updated_project["title"] == "Updated Integration Test Novel"
            
            # Get project stats
            response = client.get(f"/projects/{project_id}/stats")
            assert response.status_code == status.HTTP_200_OK
            stats = response.json()
            assert stats["project_id"] == project_id
            assert stats["title"] == "Updated Integration Test Novel"
            
            # Delete project
            response = client.delete(f"/projects/{project_id}")
            assert response.status_code == status.HTTP_200_OK
            delete_response = response.json()
            assert delete_response["success"] is True
    
    def test_get_all_projects_integration(self, db_session):
        """Test retrieving all projects with actual data."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # Create multiple projects
            projects_data = [
                {"title": "Project 1", "genre": "Fantasy"},
                {"title": "Project 2", "genre": "Sci-Fi"},
                {"title": "Project 3", "genre": "Romance"}
            ]
            
            created_ids = []
            for project_data in projects_data:
                response = client.post("/projects/", json=project_data)
                assert response.status_code == status.HTTP_201_CREATED
                created_ids.append(response.json()["id"])
            
            # Retrieve all projects
            response = client.get("/projects/")
            assert response.status_code == status.HTTP_200_OK
            projects = response.json()
            assert len(projects) == 3
            
            # Verify we can retrieve each project individually
            for project_id in created_ids:
                response = client.get(f"/projects/{project_id}")
                assert response.status_code == status.HTTP_200_OK
    
    def test_error_scenarios_integration(self, db_session):
        """Test error scenarios with actual database."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # Test getting non-existent project
            response = client.get("/projects/99999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test updating non-existent project
            response = client.put("/projects/99999", json={"title": "New Title"})
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test deleting non-existent project
            response = client.delete("/projects/99999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test invalid project ID
            response = client.get("/projects/0")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY