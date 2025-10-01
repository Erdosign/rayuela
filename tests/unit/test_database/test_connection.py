import pytest
import os
from unittest.mock import patch, MagicMock
from app.database.connection import create_database, get_session, get_db, DATABASE_URL

def test_database_url_default():
    """Test that DATABASE_URL falls back to SQLite when env var not set"""
    with patch.dict(os.environ, {}, clear=True):
        from importlib import reload
        import app.database.connection
        reload(app.database.connection)
        # Use more flexible path comparison
        url = app.database.connection.DATABASE_URL
        assert "app/database/database.db" in url.replace("\\", "/")

def test_database_url_from_env():
    """Test that DATABASE_URL uses environment variable when set"""
    test_url = "sqlite:///test.db"
    with patch.dict(os.environ, {"DATABASE_URL": test_url}):
        from importlib import reload
        import app.database.connection
        reload(app.database.connection)
        assert app.database.connection.DATABASE_URL == test_url

def test_create_database():
    """Test database creation function"""
    print("DEBUG: Starting test_create_database")
    
    # Let's see what the actual function looks like
    import inspect
    print(f"DEBUG: create_database source: {inspect.getsource(create_database)}")
    
    with patch('app.database.connection.get_engine') as mock_get_engine:
        print("DEBUG: Mock set up")
        # Set up the mock engine
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        # Call the function
        engine = create_database()
        print(f"DEBUG: create_database returned: {engine}")
        print(f"DEBUG: mock_get_engine called: {mock_get_engine.called}")
        print(f"DEBUG: mock_get_engine call count: {mock_get_engine.call_count}")
        
        # Verify the correct calls were made
        mock_get_engine.assert_called_once()

def test_get_session():
    """Test session creation"""
    # Mock get_engine and sessionmaker
    with patch('app.database.connection.get_engine') as mock_get_engine:
        with patch('app.database.connection.sessionmaker') as mock_sessionmaker:
            # Set up mocks
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine
            
            mock_session_class = MagicMock()
            mock_session_instance = MagicMock()
            mock_sessionmaker.return_value = mock_session_class
            mock_session_class.return_value = mock_session_instance
            
            # Call the function
            session = get_session()
            
            # Verify the correct calls were made
            mock_get_engine.assert_called_once()
            mock_sessionmaker.assert_called_once_with(
                autocommit=False, 
                autoflush=False, 
                bind=mock_engine
            )
            mock_session_class.assert_called_once()
            assert session == mock_session_instance

def test_get_db_generator():
    """Test the get_db dependency generator"""
    with patch('app.database.connection.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Test the generator
        generator = get_db()
        db = next(generator)
        
        assert db == mock_session
        mock_get_session.assert_called_once()
        
        # Test cleanup
        try:
            next(generator)
        except StopIteration:
            pass
        
        mock_session.close.assert_called_once()

def test_get_db_with_exception():
    """Test that session is closed even if exception occurs"""
    with patch('app.database.connection.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Simulate exception during usage
        try:
            for db in get_db():
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        mock_session.close.assert_called_once()