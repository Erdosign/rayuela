import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.novel import Project
from app.crud.novel_crud import ProjectCRUD
from datetime import datetime

class TestProjectCRUD:
    @pytest.fixture
    def db_session(self):
        """Create a temporary database for testing."""
        engine = create_engine('sqlite:///:memory:')
        Project.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_create_project(self, db_session):
        """Test creating a new project."""
        project = ProjectCRUD.create(
            db=db_session,
            title="Test Novel",
            description="A test novel",
            author="Test Author",
            genre="Fantasy"
        )
        
        assert project.id is not None
        assert project.title == "Test Novel"
        assert project.description == "A test novel"
        assert project.author == "Test Author"
        assert project.genre == "Fantasy"
        assert project.is_active == True
        assert isinstance(project.created_at, datetime)

    def test_get_project_by_id(self, db_session):
        """Test retrieving a project by ID."""
        # Create a project first
        project = ProjectCRUD.create(db_session, "Test Novel")
        
        # Retrieve it
        retrieved = ProjectCRUD.get_by_id(db_session, project.id)
        
        assert retrieved is not None
        assert retrieved.id == project.id
        assert retrieved.title == "Test Novel"

    def test_get_project_by_id_not_found(self, db_session):
        """Test retrieving a non-existent project."""
        retrieved = ProjectCRUD.get_by_id(db_session, 999)
        assert retrieved is None

    def test_get_all_projects(self, db_session):
        """Test retrieving all projects."""
        # Create multiple projects
        ProjectCRUD.create(db_session, "Novel 1")
        ProjectCRUD.create(db_session, "Novel 2")
        
        projects = ProjectCRUD.get_all(db_session)
        
        assert len(projects) == 2
        assert projects[0].title == "Novel 1"
        assert projects[1].title == "Novel 2"

    def test_get_all_active_projects_only(self, db_session):
        """Test retrieving only active projects."""
        # Create active and inactive projects
        project1 = ProjectCRUD.create(db_session, "Active Novel")
        project2 = ProjectCRUD.create(db_session, "Inactive Novel")
        ProjectCRUD.delete(db_session, project2.id)
        
        projects = ProjectCRUD.get_all(db_session, active_only=True)
        
        assert len(projects) == 1
        assert projects[0].title == "Active Novel"

    def test_update_project(self, db_session):
        """Test updating project attributes."""
        project = ProjectCRUD.create(db_session, "Original Title")
        
        updated = ProjectCRUD.update(
            db_session, 
            project.id, 
            title="Updated Title",
            description="New description",
            genre="Sci-Fi"
        )
        
        assert updated.title == "Updated Title"
        assert updated.description == "New description"
        assert updated.genre == "Sci-Fi"
        assert updated.updated_at > project.created_at

    def test_update_project_not_found(self, db_session):
        """Test updating a non-existent project."""
        updated = ProjectCRUD.update(db_session, 999, title="New Title")
        assert updated is None

    def test_soft_delete_project(self, db_session):
        """Test soft deleting a project."""
        project = ProjectCRUD.create(db_session, "To Delete")
        
        result = ProjectCRUD.delete(db_session, project.id)
        
        assert result == True
        
        # Verify it's marked as inactive
        deleted_project = ProjectCRUD.get_by_id(db_session, project.id)
        assert deleted_project.is_active == False
        
        # Verify it doesn't appear in active-only queries
        active_projects = ProjectCRUD.get_all(db_session, active_only=True)
        assert len(active_projects) == 0

    def test_delete_project_not_found(self, db_session):
        """Test deleting a non-existent project."""
        result = ProjectCRUD.delete(db_session, 999)
        assert result == False