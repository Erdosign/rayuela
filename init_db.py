#!/usr/bin/env python3
"""
Database initialization script for the novel writing app.
Run this script to create the database and tables.
"""

from app.database.connection import create_database, get_session
from app.crud.novel_crud import ProjectCRUD, ChapterCRUD, SceneCRUD

def initialize_app():
    """Initialize the application and database."""
    print("Creating database and tables...")
    create_database()
    print("Database initialized successfully!")

def create_sample_data():
    """Create sample data for testing."""
    db = get_session()
    
    try:
        print("Creating sample data...")
        
        # Create a new project
        project = ProjectCRUD.create(
            db, 
            title="My Epic Novel",
            description="A thrilling adventure story",
            author="Jane Writer",
            genre="Fantasy"
        )
        print(f"✓ Created project: {project.title}")
        
        # Create chapters
        chapter1 = ChapterCRUD.create(
            db, 
            project.id, 
            "The Beginning",
            "Our hero's journey starts"
        )
        chapter2 = ChapterCRUD.create(
            db, 
            project.id, 
            "The Middle",
            "Challenges arise"
        )
        print(f"✓ Created chapters: {chapter1.title}, {chapter2.title}")
        
        # Create scenes
        scene1 = SceneCRUD.create(
            db,
            chapter1.id,
            "Opening Scene",
            "It was a dark and stormy night. The rain pelted against the windows of the old manor house, and somewhere in the distance, a wolf howled mournfully. Inside, by the flickering candlelight, our protagonist sat hunched over an ancient tome, unaware that their life was about to change forever.",
            "Atmospheric opening that sets the mood"
        )
        scene2 = SceneCRUD.create(
            db,
            chapter1.id,
            "Character Introduction",
            "The protagonist emerged from the shadows, revealing piercing blue eyes and a determined expression. Years of training had led to this moment, and there was no turning back now.",
            "First glimpse of the hero"
        )
        scene3 = SceneCRUD.create(
            db,
            chapter2.id,
            "The Challenge",
            "The ancient door creaked open, revealing a chamber filled with mysterious artifacts. But guarding them was a creature unlike any they had ever seen - part dragon, part machine, with eyes that glowed like molten gold.",
            "First major obstacle"
        )
        
        print(f"✓ Created scenes: {scene1.title}, {scene2.title}, {scene3.title}")
        
        # Demonstrate the word count tracking
        db.refresh(project)
        print(f"✓ Project word count: {project.current_word_count} words")
        
        print("\n🎉 Sample data created successfully!")
        print(f"📖 Project: {project.title}")
        print(f"📚 Chapters: {len(project.chapters)}")
        print(f"📝 Total scenes: {sum(len(ch.scenes) for ch in project.chapters)}")
        print(f"📊 Word count: {project.current_word_count} words")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    # Initialize database
    initialize_app()
    
    # Check if user wants sample data
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        create_sample_data()
    else:
        print("\nTo create sample data, run: python init_db.py --sample")
        
    print("\n🚀 Ready to start your novel writing app!")
