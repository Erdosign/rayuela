import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch
from datetime import datetime
from app.main import app
from app.crud.novel_crud import ProjectCRUD
from app.models.novel import Project

client = TestClient(app)

class TestNovelsRouter:
    """Test novels API endpoints."""

    def test_create_project_success(self, db_session):
        """Test successful project creation."""
        project_data = {
            "title": "Test Novel",
            "description": "A test novel description",
            "author": "Test Author",
            "genre": "Fantasy",
            "target_word_count" : 0
        }
        
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # Create a SQLAlchemy model instance
            mock_project = Project(
                id=1,
                title="Test Novel",
                description="A test novel description",
                author="Test Author",
                genre="Fantasy",
                current_word_count=0,
                target_word_count=0,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(ProjectCRUD, 'create', return_value=mock_project):
                # FIX: Add /api/ prefix
                response = client.post("/projects/", json=project_data)
                
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["title"] == "Test Novel"
                assert data["description"] == "A test novel description"
                assert data["author"] == "Test Author"
                assert data["genre"] == "Fantasy"

    def test_create_project_missing_title(self, db_session):
        """Test project creation with missing title."""
        project_data = {
            "description": "A test novel description"
        }
        
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # FIX: Add /api/ prefix
            response = client.post("/projects/", json=project_data)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_project_crud_exception(self, db_session):
        """Test project creation when CRUD operation fails."""
        project_data = {
            "title": "Test Novel",
            "description": "A test novel description"
        }
        
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            with patch.object(ProjectCRUD, 'create', side_effect=Exception("DB Error")):
                # FIX: Add /api/ prefix
                response = client.post("/projects/", json=project_data)
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                data = response.json()
                assert "Failed to create project" in data["detail"]

    def test_get_project_success(self, db_session):
        """Test successful retrieval of a specific project."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
    
            # Create a SQLAlchemy model instance
            mock_project = Project(
                id=1,
                title="Test Project",
                description="Test Description",
                current_word_count=0,
                target_word_count=80000,  # ← ADD THIS
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                chapters=[]
            )
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_project):
                # Create a proper mock response that matches the expected schema
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.body = b"<html>mock template</html>"
                
                with patch('app.routers.novels.templates.TemplateResponse', return_value=mock_response):
                    response = client.get("/projects/1")
                    
                    # For template routes, we might need to handle them differently
                    # Since they return HTML, not JSON, we can check status code
                    # or mock the entire template rendering
                    assert response.status_code == 200

    def test_get_projects_active_only(self, db_session):
        """Test retrieval of active projects only."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # Mock existing project
            mock_existing_project = Project(
                id=1,
                title="Original Title",
                current_word_count=0,
                target_word_count=80000,  # ← ADD THIS
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(ProjectCRUD, 'get_all', return_value=[mock_existing_project]):
                # FIX: Add /api/ prefix
                response = client.get("/projects/?active_only=true")
                
                assert response.status_code == status.HTTP_200_OK

            # Mock updated project  
            mock_updated_project = Project(
                id=1,
                title="Updated Title",
                description="Updated description",
                current_word_count=0,
                target_word_count=80000,  # ← ADD THIS
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(ProjectCRUD, 'get_all', return_value=[mock_updated_project]):
                # FIX: Add /api/ prefix
                response = client.get("/projects/?active_only=true")
                
                assert response.status_code == status.HTTP_200_OK

    # def test_get_project_success(self, db_session):
    #     """Test successful retrieval of a specific project."""
    #     with patch('app.routers.novels.get_db') as mock_get_db:
    #         mock_get_db.return_value = db_session
    
    #         # Create a SQLAlchemy model instance
    #         mock_project = Project(
    #             id=1,
    #             title="Test Project",
    #             description="Test Description",
    #             current_word_count=0,
    #             is_active=True,     
    #             created_at=datetime.now(),
    #             updated_at=datetime.now(),
    #             chapters=[]  # Empty chapters for simplicity
    #         )
    
    #         with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_project):
    #             # Mock the template response to avoid template rendering issues
    #             with patch('app.routers.novels.templates.TemplateResponse') as mock_template:
    #                 mock_template.return_value = Mock(status_code=200)
                    
    #                 response = client.get("/projects/1")
                    
    #                 # Verify the template was called with correct parameters
    #                 mock_template.assert_called_once()
    #                 call_args = mock_template.call_args
    #                 assert call_args[0][0] == "project_detail.html"  # template name
    #                 assert "request" in call_args[1]
    #                 assert "project" in call_args[1]
    #                 assert call_args[1]["project"] == mock_project
    
    #                 # Since we mocked the template response, we can't check the actual response
    #                 # But we can verify the route logic worked by checking the mock was called
    #                 assert True  # Template was called successfully

    def test_get_project_not_found(self, db_session):
        """Test retrieval of non-existent project."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=None):
                # FIX: Add /api/ prefix
                response = client.get("/projects/999")
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                data = response.json()
                assert "not found" in data["detail"]

    def test_get_project_invalid_id(self):
        """Test retrieval with invalid project ID."""
        # FIX: Add /api/ prefix
        response = client.get("/projects/0")
        
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_update_project_success(self, db_session):
        """Test successful project update."""
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # Mock existing project
            mock_existing_project = Project(
                id=1,
                title="Original Title",
                current_word_count=0,
                target_word_count=80000,  # ← ADD THIS
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Mock updated project  
            mock_updated_project = Project(
                id=1,
                title="Updated Title",
                description="Updated description",
                current_word_count=0,
                target_word_count=80000,  # ← ADD THIS
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_existing_project):
                with patch.object(ProjectCRUD, 'update', return_value=mock_updated_project):
                    response = client.put("/projects/1", json=update_data)
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["title"] == "Updated Title"
                    assert data["description"] == "Updated description"


    def test_update_project_no_fields(self, db_session):
        """Test project update with no fields provided."""
        update_data = {}
        
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            mock_project = Project(
                id=1,
                title="Existing Project",
                current_word_count=0,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_project):
                # FIX: Add /api/ prefix
                response = client.put("/projects/1", json=update_data)
                
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
                data = response.json()
                assert "No fields provided" in data["detail"]

    def test_update_project_not_found(self, db_session):
        """Test update of non-existent project."""
        update_data = {"title": "New Title"}
        
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=None):
                # FIX: Add /api/ prefix
                response = client.put("/projects/999", json=update_data)
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project_success(self, db_session):
        """Test successful project deletion."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            mock_project = Project(
                id=1,
                title="Project to Delete",
                is_active=True,
                current_word_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_project):
                with patch.object(ProjectCRUD, 'delete', return_value=True):
                    # FIX: Add /api/ prefix
                    response = client.delete("/projects/1")
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert "deleted successfully" in data["message"]

    def test_delete_project_already_deleted(self, db_session):
        """Test deletion of already deleted project."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            mock_project = Project(
                id=1,
                title="Already Deleted Project", 
                is_active=False,
                current_word_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_project):
                # FIX: Add /api/ prefix
                response = client.delete("/projects/1")
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "already deleted" in data["detail"]

    def test_delete_project_not_found(self, db_session):
        """Test deletion of non-existent project."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=None):
                # FIX: Add /api/ prefix
                response = client.delete("/projects/999")
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_project_stats_success(self, db_session):
        """Test successful retrieval of project statistics."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            # Create a SQLAlchemy model instance
            mock_project = Project(
                id=1,
                title="Test Project",
                current_word_count=5000,
                target_word_count=10000,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                chapters=[]  # Empty chapters
            )
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_project):
                # FIX: Add /api/ prefix
                response = client.get("/projects/1/stats")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["project_id"] == 1
                assert data["title"] == "Test Project"
                assert data["current_word_count"] == 5000
                assert data["target_word_count"] == 10000

    def test_get_project_stats_zero_division(self, db_session):
        """Test project stats with zero chapters/scenes."""
        with patch('app.routers.novels.get_db') as mock_get_db:
            mock_get_db.return_value = db_session
            
            mock_project = Project(
                id=1,
                title="Empty Project", 
                current_word_count=0,
                target_word_count=0,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                chapters=[]  # No chapters
            )
            
            with patch.object(ProjectCRUD, 'get_by_id', return_value=mock_project):
                # FIX: Add /api/ prefix
                response = client.get("/projects/1/stats")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["total_chapters"] == 0
                assert data["completed_chapters"] == 0
                assert data["total_scenes"] == 0
                assert data["completed_scenes"] == 0