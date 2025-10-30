import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.novel import Project, Chapter
from app.crud.novel_crud import ProjectCRUD, ChapterCRUD, SceneCRUD
from datetime import datetime

@pytest.fixture
def sample_project_and_chapter(db_session):
    """Create sample project and chapter for tests."""
    project = ProjectCRUD.create(db_session, "Test Project")
    chapter = ChapterCRUD.create(db_session, project.id, "Test Chapter")
    return project, chapter

class TestChapterCRUD:
    @pytest.fixture
    def db_session(self):
        """Create a temporary database for testing."""
        engine = create_engine('sqlite:///:memory:')
        Project.metadata.create_all(engine)
        Chapter.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def sample_project(self, db_session):
        """Create a sample project for chapter tests."""
        return ProjectCRUD.create(db_session, "Test Project")

    def test_create_chapter(self, db_session, sample_project):
        """Test creating a new chapter."""
        chapter = ChapterCRUD.create(
            db=db_session,
            project_id=sample_project.id,
            title="Chapter 1",
            description="First chapter"
        )
        
        assert chapter.id is not None
        assert chapter.title == "Chapter 1"
        assert chapter.description == "First chapter"
        assert chapter.project_id == sample_project.id
        assert chapter.order_index == 1
        

    def test_create_multiple_chapters_order(self, db_session, sample_project):
        """Test that chapters get correct order indices."""
        chapter1 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 1")
        chapter2 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 2")
        
        assert chapter1.order_index == 1
        assert chapter2.order_index == 2

    def test_get_chapter_by_id(self, db_session, sample_project):
        """Test retrieving a chapter by ID."""
        chapter = ChapterCRUD.create(db_session, sample_project.id, "Test Chapter")
        
        retrieved = ChapterCRUD.get_by_id(db_session, chapter.id)
        
        assert retrieved is not None
        assert retrieved.id == chapter.id
        assert retrieved.title == "Test Chapter"

    def test_get_chapters_by_project(self, db_session, sample_project):
        """Test retrieving all chapters for a project."""
        ChapterCRUD.create(db_session, sample_project.id, "Chapter 1")
        ChapterCRUD.create(db_session, sample_project.id, "Chapter 2")
        
        chapters = ChapterCRUD.get_by_project(db_session, sample_project.id)
        
        assert len(chapters) == 2
        assert chapters[0].title == "Chapter 1"
        assert chapters[1].title == "Chapter 2"
        assert chapters[0].order_index == 1
        assert chapters[1].order_index == 2

    def test_update_chapter_order_move_down(self, db_session, sample_project):
        """Test updating chapter order (moving down)."""
        # Create chapters
        chapter1 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 1")
        chapter2 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 2")
        chapter3 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 3")
        
        # Move chapter1 to position 3
        result = ChapterCRUD.update_order(db_session, chapter1.id, 3)
        
        assert result == True
        
        # Verify new order
        chapters = ChapterCRUD.get_by_project(db_session, sample_project.id)
        assert chapters[0].title == "Chapter 2"  # Now first
        assert chapters[1].title == "Chapter 3"  # Now second  
        assert chapters[2].title == "Chapter 1"  # Now third
        
        assert chapters[0].order_index == 1
        assert chapters[1].order_index == 2
        assert chapters[2].order_index == 3

    def test_update_chapter_order_move_up(self, db_session, sample_project):
        """Test updating chapter order (moving up)."""
        # Create chapters
        chapter1 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 1")
        chapter2 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 2")
        chapter3 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 3")
        
        # Move chapter3 to position 1
        result = ChapterCRUD.update_order(db_session, chapter3.id, 1)
        
        assert result == True
        
        # Verify new order
        chapters = ChapterCRUD.get_by_project(db_session, sample_project.id)
        assert chapters[0].title == "Chapter 3"  # Now first
        assert chapters[1].title == "Chapter 1"  # Now second  
        assert chapters[2].title == "Chapter 2"  # Now third

    def test_update_chapter(self, db_session, sample_project):
        """Test updating chapter attributes."""
        chapter = ChapterCRUD.create(db_session, sample_project.id, "Original Title")
        
        updated = ChapterCRUD.update(
            db_session, 
            chapter.id, 
            title="Updated Title",
            description="New description"
        )
        
        assert updated.title == "Updated Title"
        assert updated.description == "New description"
        assert updated.updated_at > chapter.created_at

    def test_update_chapter_ignore_order_index(self, db_session, sample_project):
        """Test that order_index cannot be updated via update method."""
        chapter = ChapterCRUD.create(db_session, sample_project.id, "Test Chapter")
        
        updated = ChapterCRUD.update(db_session, chapter.id, order_index=999)
        
        # Order index should remain unchanged
        assert updated.order_index == 1

    def test_delete_chapter_and_reorder(self, db_session, sample_project):
        """Test deleting a chapter and reordering remaining ones."""
        chapter1 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 1")
        chapter2 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 2")
        chapter3 = ChapterCRUD.create(db_session, sample_project.id, "Chapter 3")
        
        # Delete chapter2
        result = ChapterCRUD.delete(db_session, chapter2.id)
        
        assert result == True
        
        # Verify chapters were reordered
        chapters = ChapterCRUD.get_by_project(db_session, sample_project.id)
        assert len(chapters) == 2
        assert chapters[0].title == "Chapter 1"
        assert chapters[1].title == "Chapter 3"
        assert chapters[0].order_index == 1
        assert chapters[1].order_index == 2

    def test_delete_chapter_not_found(self, db_session):
        """Test deleting a non-existent chapter."""
        result = ChapterCRUD.delete(db_session, 999)
        assert result == False
        
    def test_update_project_word_count(self, db_session):
        """Test that project word count is updated correctly."""
        # Create project and chapters
        project = ProjectCRUD.create(db_session, "Test Project")
        chapter1 = ChapterCRUD.create(db_session, project.id, "Chapter 1")
        chapter2 = ChapterCRUD.create(db_session, project.id, "Chapter 2")
        
        # Set initial word counts manually
        chapter1.word_count = 100
        chapter2.word_count = 200
        db_session.commit()
        
        # Call the internal method
        ChapterCRUD._update_project_word_count(db_session, project.id)
        
        # Refresh and verify
        db_session.refresh(project)
        assert project.current_word_count == 300  # 100 + 200
        
    def test_update_project_word_count_empty(self, db_session):
        """Test project word count with no chapters."""
        project = ProjectCRUD.create(db_session, "Empty Project")
        
        # Call the internal method
        ChapterCRUD._update_project_word_count(db_session, project.id)
        
        # Refresh and verify
        db_session.refresh(project)
        assert project.current_word_count == 0
        
    def test_update_project_word_count_none_values(self, db_session):
        """Test project word count with None values in chapters."""
        project = ProjectCRUD.create(db_session, "Test Project")
        chapter1 = ChapterCRUD.create(db_session, project.id, "Chapter 1")
        chapter2 = ChapterCRUD.create(db_session, project.id, "Chapter 2")
        
        # Set one chapter to None word count
        chapter1.word_count = None
        chapter2.word_count = 150
        db_session.commit()
        
        # Call the internal method
        ChapterCRUD._update_project_word_count(db_session, project.id)
        
        # Refresh and verify (None should be treated as 0)
        db_session.refresh(project)
        assert project.current_word_count == 150
        
    def test_update_order_invalid_chapter(self, db_session):
        """Test updating order for non-existent chapter."""
        result = ChapterCRUD.update_order(db_session, 99999, 1)
        assert result == False
        
    def test_update_chapter_word_count_directly(self, db_session, sample_project_and_chapter):
        """Test the internal _update_chapter_word_count method directly."""
        project, chapter = sample_project_and_chapter
        
        # Create scenes with word counts
        scene1 = SceneCRUD.create(db_session, chapter.id, content="Four words here now")
        scene2 = SceneCRUD.create(db_session, chapter.id, content="Three words here")
        
        # Call the internal method directly
        ChapterCRUD._update_chapter_word_count(db_session, chapter.id)
        
        # Verify the chapter word count was updated
        db_session.refresh(chapter)
        assert chapter.word_count == 7
        
    def test_update_chapter_word_count_no_chapter(self, db_session):
        """Test _update_chapter_word_count with non-existent chapter."""
        # Should not raise an error
        ChapterCRUD._update_chapter_word_count(db_session, 99999)
        
    def test_update_scene_order_invalid_scene(self, db_session):
        """Test updating order for non-existent scene."""
        result = SceneCRUD.update_order(db_session, 99999, 1)
        assert result == False  # This would cover line 298