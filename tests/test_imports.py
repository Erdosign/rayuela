def test_imports():
    """Test that basic imports work"""
    try:
        from app.models.novel import Project, Chapter, Scene
        print("✓ Models import successfully")
        
        from app.crud.novel_crud import ProjectCRUD, ChapterCRUD, SceneCRUD
        print("✓ CRUD imports successfully")
        
        from app.database.connection import Base, create_database
        print("✓ Database imports successfully")
        
        assert True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        assert False, f"Import error: {e}"