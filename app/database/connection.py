from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from pathlib import Path

Base = declarative_base()

# Improved path handling
def get_database_url():
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # Ensure database directory exists
    db_path = Path("app/database/database.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.absolute()}"

DATABASE_URL = get_database_url()

# Single engine instance
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        # SQLite doesn't support connection pooling parameters
        # Use simple engine creation for SQLite
        if DATABASE_URL.startswith("sqlite"):
            _engine = create_engine(DATABASE_URL, echo=False)
        else:
            # For other databases (PostgreSQL, MySQL), use connection pooling
            _engine = create_engine(
                DATABASE_URL, 
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
    return _engine

def create_database():
    """Create all tables in the database."""
    # Import models here to ensure they're registered with Base
    from app.models import novel
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine

def get_session():
    """Get a database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_db():
    """Dependency to get DB session for FastAPI."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
