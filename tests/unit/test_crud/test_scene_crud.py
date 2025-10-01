import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.novel import Project, Chapter, Scene
from app.crud.novel_crud import ProjectCRUD, ChapterCRUD, SceneCRUD
from datetime import datetime

class TestSceneCRUD:
    @pytest.fixture
    def db_session(self):
        """Create a temporary database for testing."""
        engine = create_engine('sqlite:///:memory:')
        Project.metadata.create_all(engine)
        Chapter.metadata.create_all(engine)
        Scene.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def sample_project_and_chapter(self, db_session):
        """Create sample project and chapter for scene tests."""
        project = ProjectCRUD.create(db_session, "Test Project")
        chapter = ChapterCRUD.create(db_session, project.id, "Test Chapter")
        return project, chapter

    def test_create_scene(self, db_session, sample_project_and_chapter):
        """Test creating a new scene."""
        project, chapter = sample_project_and_chapter
        
        scene = SceneCRUD.create(
            db=db_session,
            chapter_id=chapter.id,
            title="Scene 1",
            content="This is the scene content.",
            summary="Scene summary"
        )
        
        assert scene.id is not None
        assert scene.title == "Scene 1"
        assert scene.content == "This is the scene content."
        assert scene.summary == "Scene summary"
        assert scene.chapter_id == chapter.id
        assert scene.order_index == 1
        assert scene.word_count == 5  # "This is the scene content."

    def test_create_scene_default_title(self, db_session, sample_project_and_chapter):
        """Test creating a scene with automatic title generation."""
        project, chapter = sample_project_and_chapter
        
        scene = SceneCRUD.create(db_session, chapter.id, content="Test content")
        
        assert scene.title == "Scene 1"
        assert scene.word_count == 2

    def test_create_scene_word_count_calculation(self, db_session, sample_project_and_chapter):
        """Test word count calculation for scenes."""
        project, chapter = sample_project_and_chapter
        
        # Test with content
        scene1 = SceneCRUD.create(db_session, chapter.id, content="Word1 word2 word3")
        assert scene1.word_count == 3
        
        # Test with empty content
        scene2 = SceneCRUD.create(db_session, chapter.id, content="")
        assert scene2.word_count == 0
        
        # Test with None content
        scene3 = SceneCRUD.create(db_session, chapter.id, content=None)
        assert scene3.word_count == 0

    def test_get_scene_by_id(self, db_session, sample_project_and_chapter):
        """Test retrieving a scene by ID."""
        project, chapter = sample_project_and_chapter
        scene = SceneCRUD.create(db_session, chapter.id, "Test Scene")
        
        retrieved = SceneCRUD.get_by_id(db_session, scene.id)
        
        assert retrieved is not None
        assert retrieved.id == scene.id
        assert retrieved.title == "Test Scene"

    def test_get_scenes_by_chapter(self, db_session, sample_project_and_chapter):
        """Test retrieving all scenes for a chapter."""
        project, chapter = sample_project_and_chapter
        
        SceneCRUD.create(db_session, chapter.id, "Scene 1")
        SceneCRUD.create(db_session, chapter.id, "Scene 2")
        
        scenes = SceneCRUD.get_by_chapter(db_session, chapter.id)
        
        assert len(scenes) == 2
        assert scenes[0].title == "Scene 1"
        assert scenes[1].title == "Scene 2"

    def test_update_scene(self, db_session, sample_project_and_chapter):
        """Test updating scene attributes."""
        project, chapter = sample_project_and_chapter
        scene = SceneCRUD.create(db_session, chapter.id, "Original Title")
        
        updated = SceneCRUD.update(
            db_session,
            scene.id,
            title="Updated Title",
            content="New content with more words",  # This has 5 words, not 6
            summary="New summary"
            )
        
        assert updated.title == "Updated Title"
        assert updated.content == "New content with more words"
        assert updated.summary == "New summary"
        assert updated.word_count == 5  # Fixed: "New content with more words" = 5 words

    def test_update_scene_word_count_recalculation(self, db_session, sample_project_and_chapter):
        """Test that word count is recalculated when content changes."""
        project, chapter = sample_project_and_chapter
        scene = SceneCRUD.create(db_session, chapter.id, content="Original content")  # 2 words
        
        original_word_count = scene.word_count
        assert original_word_count == 2  # Verify initial count
        
        updated = SceneCRUD.update(db_session, scene.id, content="New content that has more words")  # 6 words
        
        assert updated.word_count == 6  # Fixed: "New content that has more words" = 6 words
        assert updated.word_count != original_word_count


    def test_delete_scene_and_reorder(self, db_session, sample_project_and_chapter):
        """Test deleting a scene and reordering remaining ones."""
        project, chapter = sample_project_and_chapter
        
        scene1 = SceneCRUD.create(db_session, chapter.id, "Scene 1")
        scene2 = SceneCRUD.create(db_session, chapter.id, "Scene 2")
        scene3 = SceneCRUD.create(db_session, chapter.id, "Scene 3")
        
        # Delete scene2
        result = SceneCRUD.delete(db_session, scene2.id)
        
        assert result == True
        
        # Verify scenes were reordered
        scenes = SceneCRUD.get_by_chapter(db_session, chapter.id)
        assert len(scenes) == 2
        assert scenes[0].title == "Scene 1"
        assert scenes[1].title == "Scene 3"
        assert scenes[0].order_index == 1
        assert scenes[1].order_index == 2

    def test_chapter_word_count_update_on_scene_operations(self, db_session, sample_project_and_chapter):
           """Test that chapter word count updates on scene operations."""
           project, chapter = sample_project_and_chapter
           
           # Create scenes with word counts
           scene1 = SceneCRUD.create(db_session, chapter.id, content="Four words here now")  # 4 words
           scene2 = SceneCRUD.create(db_session, chapter.id, content="Three words here")     # 3 words
           
           # Refresh chapter to get updated word count
           db_session.refresh(chapter)
           assert chapter.word_count == 7  # 4 + 3 words = 7
           
           # Update scene content
           SceneCRUD.update(db_session, scene1.id, content="Only two words")  # 3 words
           
           # Refresh chapter again
           db_session.refresh(chapter)
           assert chapter.word_count == 6  # Fixed: 3 (scene1) + 3 (scene2) = 6 words