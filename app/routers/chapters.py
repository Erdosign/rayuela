from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.crud.novel_crud import ChapterCRUD, ProjectCRUD
from app.schemas.novel import (
    Chapter, ChapterSimple, ChapterCreate, ChapterUpdate, ChapterReorder,
    StatusResponse, ReorderResponse
)

router = APIRouter(prefix="/chapters", tags=["chapters"])

@router.post("/", response_model=ChapterSimple, status_code=status.HTTP_201_CREATED)
def create_chapter(
    chapter: ChapterCreate,
    db: Session = Depends(get_db)
):
    """Create a new chapter."""
    # Verify project exists
    project = ProjectCRUD.get_by_id(db=db, project_id=chapter.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {chapter.project_id} not found"
        )
    
    try:
        db_chapter = ChapterCRUD.create(
            db=db,
            project_id=chapter.project_id,
            title=chapter.title,
            description=chapter.description
        )
        return db_chapter
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chapter: {str(e)}"
        )

@router.get("/project/{project_id}", response_model=List[ChapterSimple])
def get_chapters_by_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get all chapters for a specific project."""
    if project_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project ID must be a positive integer"
        )
    
    # Verify project exists
    project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    try:
        chapters = ChapterCRUD.get_by_project(db=db, project_id=project_id)
        return chapters
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chapters: {str(e)}"
        )

@router.get("/{chapter_id}", response_model=Chapter)
def get_chapter(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific chapter by ID with all scenes."""
    if chapter_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chapter ID must be a positive integer"
        )
    
    try:
        db_chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)
        if db_chapter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter with ID {chapter_id} not found"
            )
        return db_chapter
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chapter: {str(e)}"
        )

@router.put("/{chapter_id}", response_model=ChapterSimple)
def update_chapter(
    chapter_id: int,
    chapter: ChapterUpdate,
    db: Session = Depends(get_db)
):
    """Update a chapter."""
    if chapter_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chapter ID must be a positive integer"
        )
    
    # Check if chapter exists
    db_chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)
    if db_chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID {chapter_id} not found"
        )
    
    try:
        # Only update fields that are provided (not None)
        update_data = chapter.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields provided for update"
            )
        
        updated_chapter = ChapterCRUD.update(
            db=db,
            chapter_id=chapter_id,
            **update_data
        )
        return updated_chapter
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chapter: {str(e)}"
        )

@router.patch("/{chapter_id}/reorder", response_model=ReorderResponse)
def reorder_chapter(
    chapter_id: int,
    reorder: ChapterReorder,
    db: Session = Depends(get_db)
):
    """Reorder a chapter within its project (drag-and-drop functionality)."""
    if chapter_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chapter ID must be a positive integer"
        )
    
    # Check if chapter exists
    db_chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)
    if db_chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID {chapter_id} not found"
        )
    
    # Get total number of chapters in the project to validate new_order
    chapters_in_project = ChapterCRUD.get_by_project(db=db, project_id=db_chapter.project_id)
    max_order = len(chapters_in_project)
    
    if reorder.new_order > max_order:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid order position. Maximum allowed is {max_order}"
        )
    
    try:
        success = ChapterCRUD.update_order(
            db=db,
            chapter_id=chapter_id,
            new_order=reorder.new_order
        )
        
        if success:
            return ReorderResponse(
                success=True,
                message=f"Chapter '{db_chapter.title}' reordered successfully",
                new_order=reorder.new_order
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reorder chapter"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder chapter: {str(e)}"
        )

@router.delete("/{chapter_id}", response_model=StatusResponse)
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """Delete a chapter and all its scenes."""
    if chapter_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chapter ID must be a positive integer"
        )
    
    # Check if chapter exists
    db_chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)
    if db_chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID {chapter_id} not found"
        )
    
    chapter_title = db_chapter.title
    scenes_count = len(db_chapter.scenes)
    
    try:
        success = ChapterCRUD.delete(db=db, chapter_id=chapter_id)
        if success:
            return StatusResponse(
                success=True,
                message=f"Chapter '{chapter_title}' and {scenes_count} scene(s) deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete chapter"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chapter: {str(e)}"
        )

@router.get("/{chapter_id}/stats")
def get_chapter_stats(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """Get chapter statistics."""
    if chapter_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chapter ID must be a positive integer"
        )
    
    try:
        db_chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)
        if db_chapter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter with ID {chapter_id} not found"
            )
        
        total_scenes = len(db_chapter.scenes)
        completed_scenes = sum(1 for scene in db_chapter.scenes if scene.is_completed)
        
        return {
            "chapter_id": chapter_id,
            "title": db_chapter.title,
            "word_count": db_chapter.word_count,
            "total_scenes": total_scenes,
            "completed_scenes": completed_scenes,
            "completion_rate": round(
                (completed_scenes / total_scenes * 100) if total_scenes > 0 else 0,
                1
            ),
            "is_completed": db_chapter.is_completed,
            "order_index": db_chapter.order_index,
            "created_at": db_chapter.created_at,
            "updated_at": db_chapter.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chapter stats: {str(e)}"
        )
