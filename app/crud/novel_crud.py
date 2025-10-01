from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import List, Optional
from app.models.novel import Project, Chapter, Scene


class ProjectCRUD:
    @staticmethod
    def create(db: Session, title: str, description: str = None,
               author: str = None, genre: str = None) -> Project:
        """Create a new project."""
        project = Project(
            title=title,
            description=description,
            author=author,
            genre=genre
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_by_id(db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_all(db: Session, active_only: bool = True) -> List[Project]:
        """Get all projects."""
        query = db.query(Project)
        if active_only:
            query = query.filter(Project.is_active == True)
        return query.all()

    @staticmethod
    def update(db: Session, project_id: int, **kwargs) -> Optional[Project]:
        """Update project."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            project.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(project)
        return project

    @staticmethod
    def delete(db: Session, project_id: int) -> bool:
        """Soft delete project."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.is_active = False
            project.updated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False


class ChapterCRUD:
    @staticmethod
    def create(db: Session, project_id: int, title: str,
               description: str = None) -> Chapter:
        """Create a new chapter."""
        # Get the next order index
        max_order = db.query(func.max(Chapter.order_index)).filter(
            Chapter.project_id == project_id).scalar() or 0

        chapter = Chapter(
            title=title,
            description=description,
            project_id=project_id,
            order_index=max_order + 1
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def get_by_id(db: Session, chapter_id: int) -> Optional[Chapter]:
        """Get chapter by ID."""
        return db.query(Chapter).filter(Chapter.id == chapter_id).first()

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Chapter]:
        """Get all chapters for a project, ordered by order_index."""
        return db.query(Chapter).filter(
            Chapter.project_id == project_id
        ).order_by(Chapter.order_index).all()

    @staticmethod
    def update_order(db: Session, chapter_id: int, new_order: int) -> bool:
        """Update chapter order for drag-and-drop."""
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return False

        old_order = chapter.order_index
        project_id = chapter.project_id

        # Shift other chapters
        if new_order > old_order:
            # Moving down - shift chapters up
            db.query(Chapter).filter(
                Chapter.project_id == project_id,
                Chapter.order_index > old_order,
                Chapter.order_index <= new_order
            ).update({Chapter.order_index: Chapter.order_index - 1})
        else:
            # Moving up - shift chapters down
            db.query(Chapter).filter(
                Chapter.project_id == project_id,
                Chapter.order_index >= new_order,
                Chapter.order_index < old_order
            ).update({Chapter.order_index: Chapter.order_index + 1})

        chapter.order_index = new_order
        chapter.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True

    @staticmethod
    def update(db: Session, chapter_id: int, **kwargs) -> Optional[Chapter]:
        """Update chapter."""
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            for key, value in kwargs.items():
                if hasattr(chapter, key) and key != 'order_index':
                    setattr(chapter, key, value)
            chapter.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(chapter)
        return chapter

    @staticmethod
    def delete(db: Session, chapter_id: int) -> bool:
        """Delete chapter and reorder remaining chapters."""
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            project_id = chapter.project_id
            order_index = chapter.order_index
    
            db.delete(chapter)
    
            # Reorder remaining chapters
            db.query(Chapter).filter(
                Chapter.project_id == project_id,
                Chapter.order_index > order_index
            ).update({Chapter.order_index: Chapter.order_index - 1})
    
            db.commit()
    
            # Update project word count after chapter deletion
            ChapterCRUD._update_project_word_count(db, project_id)
            return True
        return False
    
    @staticmethod
    def _update_project_word_count(db: Session, project_id: int):
        """Update project word count based on its chapters."""
        total_words = db.query(func.sum(Chapter.word_count)).filter(
            Chapter.project_id == project_id).scalar() or 0
    
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.current_word_count = total_words
            project.updated_at = datetime.now(timezone.utc)
            db.commit()

    @staticmethod
    def _update_chapter_word_count(db: Session, chapter_id: int):
        """Update chapter word count based on its scenes."""
        total_words = db.query(func.sum(Scene.word_count)).filter(
            Scene.chapter_id == chapter_id).scalar() or 0
    
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            chapter.word_count = total_words
            
            # Update project word count
            ChapterCRUD._update_project_word_count(db, chapter.project_id)
            db.commit()


class SceneCRUD:
    @staticmethod
    def create(db: Session, chapter_id: int, title: str = None,
               content: str = None, summary: str = None) -> Scene:
        """Create a new scene."""
        # Get the next order index
        max_order = db.query(func.max(Scene.order_index)).filter(
            Scene.chapter_id == chapter_id).scalar() or 0

        scene = Scene(
            title=title or f"Scene {max_order + 1}",
            content=content,
            summary=summary,
            chapter_id=chapter_id,
            order_index=max_order + 1,
            word_count=len(content.split()) if content else 0
        )
        db.add(scene)
        db.commit()
        db.refresh(scene)

        # Update chapter word count
        SceneCRUD._update_chapter_word_count(db, chapter_id)
        return scene

    @staticmethod
    def get_by_id(db: Session, scene_id: int) -> Optional[Scene]:
        """Get scene by ID."""
        return db.query(Scene).filter(Scene.id == scene_id).first()

    @staticmethod
    def get_by_chapter(db: Session, chapter_id: int) -> List[Scene]:
        """Get all scenes for a chapter, ordered by order_index."""
        return db.query(Scene).filter(
            Scene.chapter_id == chapter_id
        ).order_by(Scene.order_index).all()

    @staticmethod
    def update_order(db: Session, scene_id: int, new_order: int) -> bool:
        """Update scene order for drag-and-drop."""
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            return False

        old_order = scene.order_index
        chapter_id = scene.chapter_id

        # Shift other scenes
        if new_order > old_order:
            # Moving down - shift scenes up
            db.query(Scene).filter(
                Scene.chapter_id == chapter_id,
                Scene.order_index > old_order,
                Scene.order_index <= new_order
            ).update({Scene.order_index: Scene.order_index - 1})
        else:
            # Moving up - shift scenes down
            db.query(Scene).filter(
                Scene.chapter_id == chapter_id,
                Scene.order_index >= new_order,
                Scene.order_index < old_order
            ).update({Scene.order_index: Scene.order_index + 1})

        scene.order_index = new_order
        scene.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True

    @staticmethod
    def update(db: Session, scene_id: int, **kwargs) -> Optional[Scene]:
        """Update scene."""
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if scene:
            for key, value in kwargs.items():
                if hasattr(scene, key) and key != 'order_index':
                    setattr(scene, key, value)

            # Update word count if content changed
            if 'content' in kwargs:
                scene.word_count = len(kwargs['content'].split()) if kwargs['content'] else 0

            scene.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(scene)

            # Update chapter word count
            SceneCRUD._update_chapter_word_count(db, scene.chapter_id)
        return scene

    @staticmethod
    def delete(db: Session, scene_id: int) -> bool:
        """Delete scene and reorder remaining scenes."""
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if scene:
            chapter_id = scene.chapter_id
            order_index = scene.order_index

            db.delete(scene)

            # Reorder remaining scenes
            db.query(Scene).filter(
                Scene.chapter_id == chapter_id,
                Scene.order_index > order_index
            ).update({Scene.order_index: Scene.order_index - 1})

            db.commit()

            # Update chapter word count
            SceneCRUD._update_chapter_word_count(db, chapter_id)
            return True
        return False

    @staticmethod
    def _update_chapter_word_count(db: Session, chapter_id: int):
        """Update chapter word count based on its scenes."""
        total_words = db.query(func.sum(Scene.word_count)).filter(
            Scene.chapter_id == chapter_id).scalar() or 0

        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            chapter.word_count = total_words

            # Update project word count
            project_total = db.query(func.sum(Chapter.word_count)).filter(
                Chapter.project_id == chapter.project_id).scalar() or 0

            project = db.query(Project).filter(Project.id == chapter.project_id).first()
            if project:
                project.current_word_count = project_total
                project.updated_at = datetime.now(timezone.utc)

            db.commit()