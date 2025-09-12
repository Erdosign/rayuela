from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    author = Column(String(255))
    genre = Column(String(100))
    target_word_count = Column(Integer, default=80000)
    current_word_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chapters = relationship("Chapter", back_populates="project", 
                          cascade="all, delete-orphan", order_by="Chapter.order_index")

    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}')>"

class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="chapters")
    scenes = relationship("Scene", back_populates="chapter", 
                         cascade="all, delete-orphan", order_by="Scene.order_index")

    def __repr__(self):
        return f"<Chapter(id={self.id}, title='{self.title}', order={self.order_index})>"

class Scene(Base):
    __tablename__ = "scenes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    summary = Column(Text)
    order_index = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, default=0)
    notes = Column(Text)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="scenes")

    def __repr__(self):
        return f"<Scene(id={self.id}, title='{self.title}', order={self.order_index})>"
