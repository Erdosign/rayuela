import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.novel import Project, Chapter, Scene
from app.crud.novel_crud import ProjectCRUD, ChapterCRUD, SceneCRUD

@pytest.fixture
def sample_project_and_chapter(db_session):
    """Create sample project and chapter for integration tests."""
    project = ProjectCRUD.create(db_session, "Test Project")
    chapter = ChapterCRUD.create(db_session, project.id, "Test Chapter")
    return project, chapter

class TestCRUDIntegration:
    @pytest.fixture
    def db_session(self):
        """Create a temporary database for integration testing."""
        engine = create_engine('sqlite:///:memory:')
        Project.metadata.create_all(engine)
        Chapter.metadata.create_all(engine)
        Scene.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_full_project_lifecycle(self, db_session):
        """Test complete project lifecycle with chapters and scenes."""
        # Create project
        project = ProjectCRUD.create(db_session, "Test Novel", "A test novel")
        
        # Create chapters
        chapter1 = ChapterCRUD.create(db_session, project.id, "Chapter 1")
        chapter2 = ChapterCRUD.create(db_session, project.id, "Chapter 2")
        
        # Create scenes
        scene1 = SceneCRUD.create(db_session, chapter1.id, "Opening", "Scene content here")  # 3 words
        scene2 = SceneCRUD.create(db_session, chapter1.id, "Conflict", "More content words")  # 3 words
        scene3 = SceneCRUD.create(db_session, chapter2.id, "Resolution", "Final content text")  # 3 words
        
        # Verify hierarchy
        projects = ProjectCRUD.get_all(db_session)
        chapters = ChapterCRUD.get_by_project(db_session, project.id)
        scenes_ch1 = SceneCRUD.get_by_chapter(db_session, chapter1.id)
        scenes_ch2 = SceneCRUD.get_by_chapter(db_session, chapter2.id)
        
        assert len(projects) == 1
        assert len(chapters) == 2
        assert len(scenes_ch1) == 2
        assert len(scenes_ch2) == 1
        
        # Verify word counts propagated correctly
        db_session.refresh(project)
        db_session.refresh(chapter1)
        db_session.refresh(chapter2)
        
        assert scene1.word_count == 3  # "Scene content here"
        assert scene2.word_count == 3  # "More content words" 
        assert scene3.word_count == 3  # "Final content text"
        assert chapter1.word_count == 6  # scene1 + scene2 = 3 + 3
        assert chapter2.word_count == 3  # scene3 = 3
        assert project.current_word_count == 9  # chapter1 + chapter2 = 6 + 3
        
        # Test deletion cascade effect
        ChapterCRUD.delete(db_session, chapter1.id)
        
        # Verify chapter1 scenes are gone
        scenes_after_delete = SceneCRUD.get_by_chapter(db_session, chapter1.id)
        assert len(scenes_after_delete) == 0
        
        # Verify word counts updated
        db_session.refresh(project)
        db_session.refresh(chapter2)
        assert project.current_word_count == 3  # Only chapter2 remains = 3 words
        
    def test_word_count_calculation(self, db_session):
        """Diagnostic test to understand word counting behavior."""
        project = ProjectCRUD.create(db_session, "Test Project")
        chapter = ChapterCRUD.create(db_session, project.id, "Test Chapter")
        
        test_cases = [
            ("Hello world", 2),
            ("  Hello   world  ", 2),  # extra spaces
            ("", 0),
            ("One", 1),
            ("New content with more words", 5),
            ("New content that has more words", 6)
        ]
        
        for content, expected in test_cases:
            scene = SceneCRUD.create(db_session, chapter.id, content=content)
            print(f"Content: '{content}' -> Expected: {expected}, Got: {scene.word_count}")
            assert scene.word_count == expected, f"Content: '{content}'"