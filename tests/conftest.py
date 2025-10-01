import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

@pytest.fixture
def db_session():
    """Create a clean database session for each test."""
    engine = create_engine('sqlite:///:memory:')
    
    # Import your Base after path is set
    from app.database.connection import Base
    from app.models.novel import Project, Chapter, Scene
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    engine.dispose()