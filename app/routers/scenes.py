from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.crud.novel_crud import SceneCRUD, ChapterCRUD
from app.schemas.novel import (
    Scene, SceneSimple, SceneCreate, SceneUpdate, SceneReorder, 
    StatusResponse, ReorderResponse
)

router = APIRouter(prefix="/scenes", tags=["scenes"])

@router.post("/", response_model=SceneSimple, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene: SceneCreate,
    db: Session = Depends(get_db)
):
    """Create a new scene."""
    # Verify chapter exists
    chapter = ChapterCRUD.get_by_id(db=db, chapter_id=scene.chapter_id)
    if chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID {scene.chapter_id} not found"
        )
    
    try:
        db_scene = SceneCRUD.create(
            db=db,
            chapter_id=scene.chapter_id,
            title=scene.title,
            content=scene.content,
            summary=scene.summary
        )
        return db_scene
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scene: {str(e)}"
        )

@router.get("/chapter/{chapter_id}", response_model=List[SceneSimple])
def get_scenes_by_chapter(
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """Get all scenes for a specific chapter."""
    if chapter_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chapter ID must be a positive integer"
        )
    
    # Verify chapter exists
    chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)
    if chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID {chapter_id} not found"
        )
    
    try:
        scenes = SceneCRUD.get_by_chapter(db=db, chapter_id=chapter_id)
        return scenes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scenes: {str(e)}"
        )

@router.get("/{scene_id}", response_model=SceneSimple)
def get_scene(
    scene_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific scene by ID."""
    if scene_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene ID must be a positive integer"
        )
    
    try:
        db_scene = SceneCRUD.get_by_id(db=db, scene_id=scene_id)
        if db_scene is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scene with ID {scene_id} not found"
            )
        return db_scene
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scene: {str(e)}"
        )

@router.put("/{scene_id}", response_model=SceneSimple)
def update_scene(
    scene_id: int,
    scene: SceneUpdate,
    db: Session = Depends(get_db)
):
    """Update a scene."""
    if scene_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene ID must be a positive integer"
        )
    
    # Check if scene exists
    db_scene = SceneCRUD.get_by_id(db=db, scene_id=scene_id)
    if db_scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene with ID {scene_id} not found"
        )
    
    try:
        # Only update fields that are provided (not None)
        update_data = scene.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields provided for update"
            )
        
        updated_scene = SceneCRUD.update(
            db=db,
            scene_id=scene_id,
            **update_data
        )
        return updated_scene
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scene: {str(e)}"
        )

@router.patch("/{scene_id}/reorder", response_model=ReorderResponse)
def reorder_scene(
    scene_id: int,
    reorder: SceneReorder,
    db: Session = Depends(get_db)
):
    """Reorder a scene within its chapter (drag-and-drop functionality)."""
    if scene_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene ID must be a positive integer"
        )
    
    # Check if scene exists
    db_scene = SceneCRUD.get_by_id(db=db, scene_id=scene_id)
    if db_scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene with ID {scene_id} not found"
        )
    
    # Get total number of scenes in the chapter to validate new_order
    scenes_in_chapter = SceneCRUD.get_by_chapter(db=db, chapter_id=db_scene.chapter_id)
    max_order = len(scenes_in_chapter)
    
    if reorder.new_order > max_order:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid order position. Maximum allowed is {max_order}"
        )
    
    try:
        success = SceneCRUD.update_order(
            db=db,
            scene_id=scene_id,
            new_order=reorder.new_order
        )
        
        if success:
            return ReorderResponse(
                success=True,
                message=f"Scene '{db_scene.title or f'Scene {scene_id}'}' reordered successfully",
                new_order=reorder.new_order
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reorder scene"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder scene: {str(e)}"
        )

@router.delete("/{scene_id}", response_model=StatusResponse)
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db)
):
    """Delete a scene."""
    if scene_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene ID must be a positive integer"
        )
    
    # Check if scene exists
    db_scene = SceneCRUD.get_by_id(db=db, scene_id=scene_id)
    if db_scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene with ID {scene_id} not found"
        )
    
    scene_title = db_scene.title or f"Scene {scene_id}"
    
    try:
        success = SceneCRUD.delete(db=db, scene_id=scene_id)
        if success:
            return StatusResponse(
                success=True,
                message=f"Scene '{scene_title}' has been deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete scene"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scene: {str(e)}"
        )

@router.get("/{scene_id}/content")
def get_scene_content(
    scene_id: int,
    db: Session = Depends(get_db)
):
    """Get scene content for editing (returns raw text)."""
    if scene_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene ID must be a positive integer"
        )
    
    try:
        db_scene = SceneCRUD.get_by_id(db=db, scene_id=scene_id)
        if db_scene is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scene with ID {scene_id} not found"
            )
        
        return {
            "scene_id": scene_id,
            "title": db_scene.title,
            "content": db_scene.content or "",
            "word_count": db_scene.word_count,
            "last_updated": db_scene.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scene content: {str(e)}"
        )

@router.put("/{scene_id}/content")
def update_scene_content(
    scene_id: int,
    content: str,
    title: str = None,
    db: Session = Depends(get_db)
):
    """Update scene content (for the editor)."""
    if scene_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene ID must be a positive integer"
        )
    
    # Check if scene exists
    db_scene = SceneCRUD.get_by_id(db=db, scene_id=scene_id)
    if db_scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene with ID {scene_id} not found"
        )
    
    try:
        update_data = {"content": content}
        if title is not None:
            update_data["title"] = title
        
        updated_scene = SceneCRUD.update(
            db=db,
            scene_id=scene_id,
            **update_data
        )
        
        return {
            "scene_id": scene_id,
            "title": updated_scene.title,
            "word_count": updated_scene.word_count,
            "message": "Scene content updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scene content: {str(e)}"
        )
