import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.novel import (
    ProjectBase, ProjectCreate, ProjectUpdate, Project, ProjectSimple,
    ChapterBase, ChapterCreate, ChapterUpdate, ChapterReorder, Chapter, ChapterSimple,
    SceneBase, SceneCreate, SceneUpdate, SceneReorder, Scene, SceneSimple,
    StatusResponse, ReorderResponse
)

class TestProjectSchemas:
    """Test cases for Project-related schemas"""
    
    def test_project_base_valid(self):
        """Test ProjectBase schema with valid data"""
        project_data = {
            "title": "Test Novel",
            "description": "A test novel description",
            "author": "Test Author",
            "genre": "Fantasy",
            "target_word_count": 50000
        }
        
        project = ProjectBase(**project_data)
        assert project.title == "Test Novel"
        assert project.description == "A test novel description"
        assert project.author == "Test Author"
        assert project.genre == "Fantasy"
        assert project.target_word_count == 50000
    
    def test_project_base_minimal(self):
        """Test ProjectBase schema with minimal required data"""
        project_data = {
            "title": "Minimal Novel"
        }
        
        project = ProjectBase(**project_data)
        assert project.title == "Minimal Novel"
        assert project.description is None
        assert project.author is None
        assert project.genre is None
        assert project.target_word_count == 80000  # Default value
    
    def test_project_base_validation(self):
        """Test ProjectBase schema field validation"""
        # Test title length constraints
        with pytest.raises(ValidationError):
            ProjectBase(title="")  # min_length=1
        
        with pytest.raises(ValidationError):
            ProjectBase(title="A" * 256)  # max_length=255
        
        # Test target_word_count validation
        with pytest.raises(ValidationError):
            ProjectBase(title="Test", target_word_count=-1)  # ge=0
    
    def test_project_create_inheritance(self):
        """Test ProjectCreate inherits from ProjectBase"""
        project_data = {
            "title": "Create Novel",
            "target_word_count": 60000
        }
        
        project_create = ProjectCreate(**project_data)
        assert project_create.title == "Create Novel"
        assert project_create.target_word_count == 60000
        # Should have same fields as ProjectBase
        assert hasattr(project_create, 'description')
        assert hasattr(project_create, 'author')
        assert hasattr(project_create, 'genre')
    
    def test_project_update_optional_fields(self):
        """Test ProjectUpdate schema allows partial updates"""
        # Test single field update
        update_data = {"title": "Updated Title"}
        project_update = ProjectUpdate(**update_data)
        assert project_update.title == "Updated Title"
        assert project_update.description is None
        
        # Test multiple fields
        update_data = {
            "title": "New Title",
            "genre": "Mystery",
            "is_active": False
        }
        project_update = ProjectUpdate(**update_data)
        assert project_update.title == "New Title"
        assert project_update.genre == "Mystery"
        assert project_update.is_active is False
        
        # Test empty update (should be allowed for PATCH)
        empty_update = ProjectUpdate()
        assert empty_update.model_dump(exclude_unset=True) == {}
    
    def test_project_response_full(self):
        """Test Project response schema with nested chapters"""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        
        response_data = {
            "id": 1,
            "title": "Response Novel",
            "description": "A novel for response testing",
            "author": "Response Author",
            "genre": "Mystery",
            "target_word_count": 60000,
            "current_word_count": 1500,
            "is_active": True,
            "created_at": test_datetime,
            "updated_at": test_datetime,
            "chapters": []
        }
        
        project = Project(**response_data)
        assert project.id == 1
        assert project.title == "Response Novel"
        assert project.current_word_count == 1500
        assert project.is_active is True
        assert project.created_at == test_datetime
        assert project.chapters == []
    
    def test_project_simple_response(self):
        """Test ProjectSimple response schema (no nested chapters)"""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        
        response_data = {
            "id": 1,
            "title": "Simple Project",
            "current_word_count": 1500,
            "is_active": True,
            "created_at": test_datetime,
            "updated_at": test_datetime
        }
        
        project = ProjectSimple(**response_data)
        assert project.id == 1
        assert project.title == "Simple Project"
        assert not hasattr(project, 'chapters')  # No nested relationships

class TestChapterSchemas:
    """Test cases for Chapter-related schemas"""
    
    def test_chapter_base_valid(self):
        """Test ChapterBase schema with valid data"""
        chapter_data = {
            "title": "Chapter 1",
            "description": "The beginning chapter"
        }
        
        chapter = ChapterBase(**chapter_data)
        assert chapter.title == "Chapter 1"
        assert chapter.description == "The beginning chapter"
    
    def test_chapter_create_required_fields(self):
        """Test ChapterCreate schema requires project_id"""
        chapter_data = {
            "title": "Chapter 1",
            "project_id": 1
        }
        
        chapter = ChapterCreate(**chapter_data)
        assert chapter.title == "Chapter 1"
        assert chapter.project_id == 1
        assert chapter.project_id > 0  # gt=0 validation
    
    def test_chapter_create_validation(self):
        """Test ChapterCreate schema field validation"""
        # Test missing project_id
        with pytest.raises(ValidationError):
            ChapterCreate(title="Chapter 1")  # Missing project_id
        
        # Test invalid project_id
        with pytest.raises(ValidationError):
            ChapterCreate(title="Chapter 1", project_id=0)  # gt=0 validation
    
    def test_chapter_update(self):
        """Test ChapterUpdate schema for partial updates"""
        update_data = {
            "title": "Updated Chapter Title",
            "is_completed": True
        }
        
        chapter_update = ChapterUpdate(**update_data)
        assert chapter_update.title == "Updated Chapter Title"
        assert chapter_update.is_completed is True
        assert chapter_update.description is None
    
    def test_chapter_reorder(self):
        """Test ChapterReorder schema for order changes"""
        reorder_data = {"new_order": 3}
        chapter_reorder = ChapterReorder(**reorder_data)
        assert chapter_reorder.new_order == 3
        
        # Test validation
        with pytest.raises(ValidationError):
            ChapterReorder(new_order=0)  # ge=1 validation
    
    def test_chapter_response_with_scenes(self):
        """Test Chapter response schema with nested scenes"""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        
        response_data = {
            "id": 1,
            "title": "Response Chapter",
            "description": "A chapter for testing",
            "project_id": 1,
            "order_index": 2,
            "word_count": 2500,
            "is_completed": False,
            "created_at": test_datetime,
            "updated_at": test_datetime,
            "scenes": []
        }
        
        chapter = Chapter(**response_data)
        assert chapter.id == 1
        assert chapter.project_id == 1
        assert chapter.order_index == 2
        assert chapter.scenes == []

class TestSceneSchemas:
    """Test cases for Scene-related schemas"""
    
    def test_scene_base_optional_fields(self):
        """Test SceneBase schema with all optional fields"""
        scene_data = {
            "title": "Opening Scene",
            "content": "This is the scene content...",
            "summary": "A summary",
            "notes": "Author notes"
        }
        
        scene = SceneBase(**scene_data)
        assert scene.title == "Opening Scene"
        assert scene.content == "This is the scene content..."
        assert scene.summary == "A summary"
        assert scene.notes == "Author notes"
    
    def test_scene_base_empty(self):
        """Test SceneBase schema with no fields (all optional)"""
        scene = SceneBase()
        assert scene.title is None
        assert scene.content is None
        assert scene.summary is None
        assert scene.notes is None
    
    def test_scene_create_required_fields(self):
        """Test SceneCreate schema requires chapter_id"""
        scene_data = {
            "title": "Scene 1",
            "chapter_id": 1
        }
        
        scene = SceneCreate(**scene_data)
        assert scene.title == "Scene 1"
        assert scene.chapter_id == 1
    
    def test_scene_update(self):
        """Test SceneUpdate schema for content updates"""
        update_data = {
            "content": "Updated scene content...",
            # "word_count": 500,  # Note: word_count not in SceneUpdate, should be ignored or raise error
            "is_completed": True
        }
        
        scene_update = SceneUpdate(**update_data)
        
        assert scene_update.content == "Updated scene content..."
        assert scene_update.is_completed is True
        assert scene_update.title is None
    
    def test_scene_reorder(self):
        """Test SceneReorder schema for order changes"""
        reorder_data = {"new_order": 5}
        scene_reorder = SceneReorder(**reorder_data)
        assert scene_reorder.new_order == 5
        
        # Test validation
        with pytest.raises(ValidationError):
            SceneReorder(new_order=0)  # ge=1 validation
    
    def test_scene_response(self):
        """Test Scene response schema"""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        
        response_data = {
            "id": 1,
            "title": "Response Scene",
            "content": "Scene content",
            "chapter_id": 1,
            "order_index": 1,
            "word_count": 150,
            "is_completed": True,
            "created_at": test_datetime,
            "updated_at": test_datetime
        }
        
        scene = Scene(**response_data)
        assert scene.id == 1
        assert scene.chapter_id == 1
        assert scene.order_index == 1
        assert scene.word_count == 150
        assert scene.is_completed is True

class TestResponseSchemas:
    """Test cases for status and response schemas"""
    
    def test_status_response(self):
        """Test StatusResponse schema"""
        status_data = {
            "success": True,
            "message": "Operation completed successfully"
        }
        
        status = StatusResponse(**status_data)
        assert status.success is True
        assert status.message == "Operation completed successfully"
    
    def test_reorder_response(self):
        """Test ReorderResponse schema"""
        reorder_data = {
            "success": True,
            "message": "Item reordered successfully",
            "new_order": 3
        }
        
        reorder = ReorderResponse(**reorder_data)
        assert reorder.success is True
        assert reorder.message == "Item reordered successfully"
        assert reorder.new_order == 3
    
    def test_from_attributes_config(self):
        """Test that response schemas have from_attributes = True"""
        # In Pydantic V2, check model_config instead of Config class
        assert hasattr(Project, 'model_config')
        assert Project.model_config.get('from_attributes') is True
        
        assert hasattr(Chapter, 'model_config')
        assert Chapter.model_config.get('from_attributes') is True
        
        assert hasattr(Scene, 'model_config')
        assert Scene.model_config.get('from_attributes') is True
        
        # Test simple schemas
        assert ProjectSimple.model_config.get('from_attributes') is True
        assert ChapterSimple.model_config.get('from_attributes') is True
        assert SceneSimple.model_config.get('from_attributes') is True

class TestSchemaIntegration:
    """Test cases for schema integration and complex scenarios"""
    
    def test_project_with_nested_chapters_and_scenes(self):
        """Test complex nested structure"""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        
        project_data = {
            "id": 1,
            "title": "Complex Project",
            "current_word_count": 5000,
            "is_active": True,
            "created_at": test_datetime,
            "updated_at": test_datetime,
            "chapters": [
                {
                    "id": 1,
                    "title": "Chapter 1",
                    "project_id": 1,
                    "order_index": 1,
                    "word_count": 2500,
                    "is_completed": False,
                    "created_at": test_datetime,
                    "updated_at": test_datetime,
                    "scenes": [
                        {
                            "id": 1,
                            "title": "Scene 1",
                            "chapter_id": 1,
                            "order_index": 1,
                            "word_count": 500,
                            "is_completed": True,
                            "created_at": test_datetime,
                            "updated_at": test_datetime
                        }
                    ]
                }
            ]
        }
        
        project = Project(**project_data)
        assert project.id == 1
        assert len(project.chapters) == 1
        assert project.chapters[0].title == "Chapter 1"
        assert len(project.chapters[0].scenes) == 1
        assert project.chapters[0].scenes[0].title == "Scene 1"
    
    def test_field_descriptions(self):
        """Test that Field descriptions are present"""
        # Use model_fields instead of __fields__ for Pydantic V2
        project_fields = ProjectCreate.model_fields
        title_field = project_fields.get("title")
        
        # Check if description exists in the field info
        if title_field and hasattr(title_field, 'description'):
            assert title_field.description is not None
        else:
            # Skip this check if descriptions aren't accessible this way
            pytest.skip("Field descriptions not accessible via model_fields in this Pydantic version")