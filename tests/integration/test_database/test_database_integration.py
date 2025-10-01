import pytest
from unittest.mock import patch
from sqlalchemy import inspect
from app.database.connection import create_database, get_session, Base
from sqlalchemy import Column, Integer, String

# Test model for integration tests
class IntegrationTestModel(Base):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

def test_integration_create_database():
    """Integration test for actual database creation using in-memory DB"""
    # Use shared in-memory SQLite database
    test_db_url = "sqlite:///:memory:"
    
    with patch('app.database.connection.DATABASE_URL', test_db_url):
        # Create database with our test model
        engine = create_database()
        
        # Verify table was created
        inspector = inspect(engine)
        assert inspector.has_table("test_model")

def test_integration_session_operations():
    """Test actual database operations with session using in-memory DB"""
    # Use shared in-memory SQLite database with cache=shared
    test_db_url = "sqlite:///:memory:?cache=shared"
    
    with patch('app.database.connection.DATABASE_URL', test_db_url):
        # Create database - this creates the engine and tables
        engine = create_database()
        
        # Test session operations - use the same engine to ensure same connection
        SessionLocal = pytest.importorskip("sqlalchemy.orm").sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        session = SessionLocal()
        
        try:
            # Create test record
            test_obj = IntegrationTestModel(name="test")
            session.add(test_obj)
            session.commit()
            
            # Verify record was saved
            result = session.query(IntegrationTestModel).first()
            assert result.name == "test"
            
        finally:
            # Always close session
            session.close()
            engine.dispose()