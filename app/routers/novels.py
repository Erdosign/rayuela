from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.crud.novel_crud import ProjectCRUD
from app.schemas.novel import (
    Project, ProjectSimple, ProjectCreate, ProjectUpdate, StatusResponse
)

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectSimple, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project."""
    try:
        db_project = ProjectCRUD.create(
            db=db,
            title=project.title,
            description=project.description,
            author=project.author,
            genre=project.genre
        )
        return db_project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/", response_model=List[ProjectSimple])
def get_projects(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all projects."""
    try:
        projects = ProjectCRUD.get_all(db=db, active_only=active_only)
        return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )

@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific project by ID with all chapters and scenes."""
    if project_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project ID must be a positive integer"
        )
    
    try:
        db_project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
        if db_project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        return db_project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project: {str(e)}"
        )

@router.put("/{project_id}", response_model=ProjectSimple)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project."""
    if project_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project ID must be a positive integer"
        )
    
    # Check if project exists
    db_project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    try:
        # Only update fields that are provided (not None)
        update_data = project.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields provided for update"
            )
        
        updated_project = ProjectCRUD.update(
            db=db,
            project_id=project_id,
            **update_data
        )
        return updated_project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete("/{project_id}", response_model=StatusResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Soft delete a project (sets is_active to False)."""
    if project_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project ID must be a positive integer"
        )
    
    # Check if project exists
    db_project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    if not db_project.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is already deleted"
        )
    
    try:
        success = ProjectCRUD.delete(db=db, project_id=project_id)
        if success:
            return StatusResponse(
                success=True,
                message=f"Project '{db_project.title}' has been deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete project"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

@router.get("/{project_id}/stats")
def get_project_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get project statistics."""
    if project_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project ID must be a positive integer"
        )
    
    try:
        db_project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
        if db_project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        total_chapters = len(db_project.chapters)
        completed_chapters = sum(1 for ch in db_project.chapters if ch.is_completed)
        total_scenes = sum(len(ch.scenes) for ch in db_project.chapters)
        completed_scenes = sum(
            sum(1 for scene in ch.scenes if scene.is_completed) 
            for ch in db_project.chapters
        )
        
        progress_percentage = 0
        if db_project.target_word_count > 0:
            progress_percentage = min(
                (db_project.current_word_count / db_project.target_word_count) * 100,
                100
            )
        
        return {
            "project_id": project_id,
            "title": db_project.title,
            "current_word_count": db_project.current_word_count,
            "target_word_count": db_project.target_word_count,
            "progress_percentage": round(progress_percentage, 1),
            "total_chapters": total_chapters,
            "completed_chapters": completed_chapters,
            "total_scenes": total_scenes,
            "completed_scenes": completed_scenes,
            "chapters_completion_rate": round(
                (completed_chapters / total_chapters * 100) if total_chapters > 0 else 0,
                1
            ),
            "scenes_completion_rate": round(
                (completed_scenes / total_scenes * 100) if total_scenes > 0 else 0,
                1
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project stats: {str(e)}"
        )
