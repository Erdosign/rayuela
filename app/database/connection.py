from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app/database/database.db")

def create_database():
    """Create all tables in the database."""
    # Import models here to ensure they're registered with Base
    from app.models import novel
    
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    return engine

def get_session():
    """Get a database session."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_db():
    """Dependency to get DB session for FastAPI."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
