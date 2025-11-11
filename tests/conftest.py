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
    # Import inside fixture to avoid circular imports
    from app.database.connection import Base
    
    # Use in-memory SQLite for tests
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False}
    )
    
    # IMPORT MODELS so tables are registered with Base
    from app.models.novel import Project, Chapter, Scene
    
    # Create all tables
    Base.metadata.drop_all(engine)  # Clean start
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
    """Create a FastAPI app with overridden dependencies."""
    # Import app INSIDE the fixture to ensure fresh instance
    from app.main import app
    from app.database.connection import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    return app

@pytest.fixture
def client(app):
    """Create a test client using the app fixture."""
    with TestClient(app) as test_client:
        yield test_client