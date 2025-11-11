import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

@pytest.fixture
def db_session():
    """Create a clean database session for each test."""
    from app.database.connection import Base
    
    # Use in-memory SQLite for tests
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False}
    )
    
    # Import models to register them
    from app.models.novel import Project, Chapter, Scene
    
    # Create all tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def app(db_session):
    """Create FastAPI app with overridden dependencies BEFORE routes are imported."""
    # IMPORTANT: Import get_db and override BEFORE importing any routers
    from app.database.connection import get_db
    from app.main import app
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override the dependency FIRST
    app.dependency_overrides[get_db] = override_get_db
    
    # NOW import and include routers (they'll get the overridden dependency)
    from app.routers import novels
    # If you have other routers, import them here too
    
    # Re-include routers to ensure they use overridden dependencies
    app.include_router(novels.router)
    
    return app

@pytest.fixture
def client(app):
    """Create a test client using the app fixture."""
    with TestClient(app) as test_client:
        yield test_client