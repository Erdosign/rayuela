from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# Base schemas
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Project title")
    description: Optional[str] = Field(None, description="Project description")
    author: Optional[str] = Field(None, max_length=255, description="Author name")
    genre: Optional[str] = Field(None, max_length=100, description="Genre")
    target_word_count: Optional[int] = Field(80000, ge=0, description="Target word count")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    target_word_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class ChapterBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Chapter title")
    description: Optional[str] = Field(None, description="Chapter description")

class ChapterCreate(ChapterBase):
    project_id: int = Field(..., gt=0, description="Project ID")

class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_completed: Optional[bool] = None

class ChapterReorder(BaseModel):
    new_order: int = Field(..., ge=1, description="New order position (1-based)")

class SceneBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Scene title")
    content: Optional[str] = Field(None, description="Scene content")
    summary: Optional[str] = Field(None, description="Scene summary")
    notes: Optional[str] = Field(None, description="Scene notes")

class SceneCreate(SceneBase):
    chapter_id: int = Field(..., gt=0, description="Chapter ID")

class SceneUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    summary: Optional[str] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None

class SceneReorder(BaseModel):
    new_order: int = Field(..., ge=1, description="New order position (1-based)")

# Response schemas
class Scene(SceneBase):
    id: int
    chapter_id: int
    order_index: int
    word_count: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Chapter(ChapterBase):
    id: int
    project_id: int
    order_index: int
    word_count: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    scenes: List[Scene] = []

    model_config = ConfigDict(from_attributes=True)

class Project(ProjectBase):
    id: int
    current_word_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    chapters: List[Chapter] = []

    model_config = ConfigDict(from_attributes=True)

# Simplified response schemas (without nested relationships)
class ProjectSimple(ProjectBase):
    id: int
    current_word_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChapterSimple(ChapterBase):
    id: int
    project_id: int
    order_index: int
    word_count: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SceneSimple(SceneBase):
    id: int
    chapter_id: int
    order_index: int
    word_count: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Status response schemas
class StatusResponse(BaseModel):
    success: bool
    message: str

class ReorderResponse(StatusResponse):
    new_order: int
