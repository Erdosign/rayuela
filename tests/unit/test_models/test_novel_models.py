import pytest
from datetime import datetime
from sqlalchemy import inspect
from app.models.novel import Project, Chapter, Scene

class TestProjectModel:
    """Test cases for Project model"""
    
    def test_project_creation(self):
        """Test basic Project creation with required fields"""
        project = Project(
            title="Test Novel",
            author="Test Author",
            genre="Fantasy"
        )
        
        assert project.title == "Test Novel"
        assert project.author == "Test Author"
        assert project.genre == "Fantasy"
        # Default values are None until persisted - this is correct SQLAlchemy behavior
        assert project.target_word_count is None  # Fixed: Default applies on persistence
        assert project.current_word_count is None  # Fixed: Default applies on persistence
        assert project.is_active is None  # Fixed: Default applies on persistence
        assert project.id is None  # Not assigned until persisted
    
    def test_project_optional_fields(self):
        """Test Project creation with optional fields"""
        project = Project(
            title="Test Novel",
            description="A test novel description",
            author="Test Author",
            genre="Sci-Fi",
            target_word_count=50000,
            current_word_count=1500,
            is_active=False
        )
        
        assert project.description == "A test novel description"
        assert project.target_word_count == 50000
        assert project.current_word_count == 1500
        assert project.is_active is False
    
    def test_project_string_representation(self):
        """Test Project __repr__ method"""
        project = Project(id=1, title="Test Novel")
        expected_repr = "<Project(id=1, title='Test Novel')>"
        assert repr(project) == expected_repr
    
    def test_project_relationships(self):
        """Test Project relationships are properly configured"""
        project = Project(title="Test Novel")
        
        # Check that chapters relationship exists and is empty
        assert hasattr(project, 'chapters')
        assert project.chapters == []  # Should be empty list by default


class TestChapterModel:
    """Test cases for Chapter model"""
    
    def test_chapter_creation(self):
        """Test basic Chapter creation with required fields"""
        chapter = Chapter(
            title="Chapter 1",
            order_index=1,
            project_id=1
        )
        
        assert chapter.title == "Chapter 1"
        assert chapter.order_index == 1
        assert chapter.project_id == 1
        assert chapter.word_count is None  # Fixed: Default applies on persistence
        assert chapter.is_completed is None  # Fixed: Default applies on persistence
        assert chapter.id is None
    
    def test_chapter_optional_fields(self):
        """Test Chapter creation with optional fields"""
        chapter = Chapter(
            title="Chapter 1",
            description="The beginning of the story",
            order_index=1,
            project_id=1,
            word_count=2500,
            is_completed=True
        )
        
        assert chapter.description == "The beginning of the story"
        assert chapter.word_count == 2500
        assert chapter.is_completed is True
    
    def test_chapter_string_representation(self):
        """Test Chapter __repr__ method"""
        chapter = Chapter(id=1, title="Chapter 1", order_index=1)
        expected_repr = "<Chapter(id=1, title='Chapter 1', order=1)>"
        assert repr(chapter) == expected_repr
    
    def test_chapter_relationships(self):
        """Test Chapter relationships are properly configured"""
        chapter = Chapter(title="Chapter 1", order_index=1, project_id=1)
        
        # Check that relationships exist
        assert hasattr(chapter, 'project')
        assert hasattr(chapter, 'scenes')
        assert chapter.scenes == []  # Should be empty list by default

class TestSceneModel:
    """Test cases for Scene model"""
    
    def test_scene_creation(self):
        """Test basic Scene creation with required fields"""
        scene = Scene(
            title="Opening Scene",
            order_index=1,
            chapter_id=1
        )
        
        assert scene.title == "Opening Scene"
        assert scene.order_index == 1
        assert scene.chapter_id == 1
        assert scene.content is None  # No default specified
        assert scene.word_count is None  # Fixed: Default applies on persistence
        assert scene.is_completed is None  # Fixed: Default applies on persistence
        assert scene.id is None
    
    def test_scene_optional_fields(self):
        """Test Scene creation with optional fields"""
        scene = Scene(
            title="Important Scene",
            content="This is the scene content...",
            summary="A summary of the scene",
            order_index=2,
            chapter_id=1,
            word_count=500,
            notes="Author's notes about this scene",
            is_completed=True
        )
        
        assert scene.content == "This is the scene content..."
        assert scene.summary == "A summary of the scene"
        assert scene.word_count == 500
        assert scene.notes == "Author's notes about this scene"
        assert scene.is_completed is True
    
    def test_scene_string_representation(self):
        """Test Scene __repr__ method"""
        scene = Scene(id=1, title="Opening Scene", order_index=1)
        expected_repr = "<Scene(id=1, title='Opening Scene', order=1)>"
        assert repr(scene) == expected_repr
    
    def test_scene_relationships(self):
        """Test Scene relationships are properly configured"""
        scene = Scene(title="Test Scene", order_index=1, chapter_id=1)
        
        # Check that chapter relationship exists
        assert hasattr(scene, 'chapter')

class TestModelRelationships:
    """Test cases for model relationships and cascading"""
    
    def test_project_chapter_relationship(self):
        """Test Project-Chapter relationship"""
        project = Project(title="Test Novel")
        chapter = Chapter(title="Chapter 1", order_index=1)
        
        # Establish relationship
        project.chapters.append(chapter)
        
        assert chapter in project.chapters
        assert chapter.project == project
    
    def test_chapter_scene_relationship(self):
        """Test Chapter-Scene relationship"""
        chapter = Chapter(title="Chapter 1", order_index=1, project_id=1)
        scene = Scene(title="Scene 1", order_index=1)
        
        # Establish relationship
        chapter.scenes.append(scene)
        
        assert scene in chapter.scenes
        assert scene.chapter == chapter
    
    def test_cascade_behavior(self):
        """Test that cascade relationships are configured correctly"""
        # This will be tested more thoroughly in integration tests
        project = Project(title="Test Novel")
        chapter = Chapter(title="Chapter 1", order_index=1)
        scene = Scene(title="Scene 1", order_index=1)
        
        # Build the relationship chain
        project.chapters.append(chapter)
        chapter.scenes.append(scene)
        
        assert len(project.chapters) == 1
        assert len(chapter.scenes) == 1