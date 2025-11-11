from fastapi import FastAPI, HTTPException, Request, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os



# Import routers
from app.routers import novels, chapters, scenes

# Import database initialization
from app.database.connection import create_database, get_db
from app.crud.novel_crud import ProjectCRUD, ChapterCRUD, SceneCRUD

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        create_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
    yield
    # Shutdown

# Create FastAPI app
app = FastAPI(
    title="Novel Writing App API",
    description="A comprehensive API for managing novel writing projects, chapters, and scenes",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with API prefix
app.include_router(novels.router)
app.include_router(chapters.router)
app.include_router(scenes.router)

# Load Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     try:
#         create_database()
#         print("✅ Database initialized successfully")
#     except Exception as e:
#         print(f"❌ Failed to initialize database: {e}")
#     yield
#     # Shutdown - you can leave this empty for now
#     # Add any cleanup logic here if needed later


# Add template filter for number formatting
def number_format(value):
    """Format numbers with commas"""
    if value is None:
        return "0"
    return f"{int(value):,}"


def timeago(dt):
    """Simple timeago filter"""
    if not dt:
        return "recently"
    from datetime import datetime
    now = datetime.utcnow()
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

    diff = now - dt
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hours ago"
    else:
        return "recently"


# Register filters
templates.env.filters["number_format"] = number_format
templates.env.filters["timeago"] = timeago
        
@app.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request, db: Session = Depends(get_db)):
    """Projects list page"""
    try:
        projects = ProjectCRUD.get_all(db=db, active_only=True)

        # Calculate additional stats for each project
        for project in projects:
            chapters = ChapterCRUD.get_by_project(db=db, project_id=project.id)
            project.chapters_count = len(chapters)
            project.scenes_count = sum(len(chapter.scenes) for chapter in chapters)
            project.word_count = project.current_word_count or 0

        total_words = sum(p.current_word_count or 0 for p in projects)
        in_progress_count = sum(1 for p in projects if (p.current_word_count or 0) > 0)
        completed_count = sum(1 for p in projects if p.current_word_count >= (p.target_word_count or 80000))

        return templates.TemplateResponse("projects_list.html", {
            "request": request,
            "projects": projects,
            "total_words": total_words,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count
        })
    except Exception as e:
        print(f"Error loading projects: {e}")
        return templates.TemplateResponse("projects_list.html", {
            "request": request,
            "projects": [],
            "total_words": 0,
            "in_progress_count": 0,
            "completed_count": 0
        })


@app.post("/projects/create")
async def create_project_form(
        request: Request,
        title: str = Form(...),
        description: str = Form(None),
        author: str = Form(None),
        genre: str = Form(None),
        target_word_count: int = Form(None),
        db: Session = Depends(get_db)
):
    """Create a new project from form submission"""
    try:
        project = ProjectCRUD.create(
            db=db,
            title=title,
            description=description,
            author=author,
            genre=genre
        )

        if target_word_count:
            ProjectCRUD.update(db=db, project_id=project.id, target_word_count=target_word_count)

        return RedirectResponse(url=f"/projects/{project.id}", status_code=303)
    except Exception as e:
        print(f"Error creating project: {e}")
        return RedirectResponse(url="/projects", status_code=303)

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Project detail page with chapters and scenes"""
    try:
        project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        chapters = ChapterCRUD.get_by_project(db=db, project_id=project_id)

        # Load scenes for each chapter
        for chapter in chapters:
            chapter.scenes = SceneCRUD.get_by_chapter(db=db, chapter_id=chapter.id)

        return templates.TemplateResponse("project_detail.html", {
            "request": request,
            "project": project,
            "chapters": chapters
        })
    except Exception as e:
        print(f"Error loading project detail: {e}")
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/projects/{project_id}/chapters/{chapter_id}", response_class=HTMLResponse)
async def chapter_detail(request: Request, project_id: int, chapter_id: int, db: Session = Depends(get_db)):
    """Chapter detail page with scenes"""
    try:
        project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
        chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)

        if not project or not chapter:
            raise HTTPException(status_code=404, detail="Project or chapter not found")

        scenes = SceneCRUD.get_by_chapter(db=db, chapter_id=chapter_id)

        return templates.TemplateResponse("chapter_detail.html", {
            "request": request,
            "project": project,
            "chapter": chapter,
            "scenes": scenes
        })
    except Exception as e:
        print(f"Error loading chapter detail: {e}")
        raise HTTPException(status_code=404, detail="Chapter not found")


@app.get("/projects/{project_id}/chapters/{chapter_id}/scenes/{scene_id}/edit", response_class=HTMLResponse)
async def scene_editor(request: Request, project_id: int, chapter_id: int, scene_id: int,
                       db: Session = Depends(get_db)):
    """Scene editor page"""
    try:
        project = ProjectCRUD.get_by_id(db=db, project_id=project_id)
        chapter = ChapterCRUD.get_by_id(db=db, chapter_id=chapter_id)
        scene = SceneCRUD.get_by_id(db=db, scene_id=scene_id)

        if not project or not chapter or not scene:
            raise HTTPException(status_code=404, detail="Project, chapter, or scene not found")

        return templates.TemplateResponse("scene_editor.html", {
            "request": request,
            "project": project,
            "chapter": chapter,
            "scene": scene
        })
    except Exception as e:
        print(f"Error loading scene editor: {e}")
        raise HTTPException(status_code=404, detail="Scene not found")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint with API information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Novel Writing App API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
            .get { background-color: #61affe; }
            .post { background-color: #49cc90; }
            .put { background-color: #fca130; }
            .patch { background-color: #50e3c2; }
            .delete { background-color: #f93e3e; }
            h1 { color: #333; }
            h2 { color: #666; border-bottom: 2px solid #eee; }
        </style>
    </head>
    <body>
        <h1>📚 Novel Writing App API</h1>
        <p>Welcome to the Novel Writing App API! This API helps you manage your novel writing projects, chapters, and scenes.</p>
        
        <h2>📖 API Documentation</h2>
        <ul>
            <li><a href="/api/docs" target="_blank">Interactive API Documentation (Swagger)</a></li>
            <li><a href="/api/redoc" target="_blank">ReDoc Documentation</a></li>
        </ul>
        
        <h2>🚀 Quick Start Endpoints</h2>
        
        <h3>Projects</h3>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/projects</code> - Get all projects
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/projects</code> - Create a new project
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/projects/{project_id}</code> - Get project details
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/projects/{project_id}</code> - Update project
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span> <code>/api/projects/{project_id}</code> - Delete project
        </div>
        
        <h3>Chapters</h3>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/chapters/project/{project_id}</code> - Get chapters for a project
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/chapters</code> - Create a new chapter
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/chapters/{chapter_id}</code> - Update chapter
        </div>
        <div class="endpoint">
            <span class="method patch">PATCH</span> <code>/api/chapters/{chapter_id}/reorder</code> - Reorder chapter
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span> <code>/api/chapters/{chapter_id}</code> - Delete chapter
        </div>
        
        <h3>Scenes</h3>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/scenes/chapter/{chapter_id}</code> - Get scenes for a chapter
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/scenes</code> - Create a new scene
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/scenes/{scene_id}</code> - Get scene details
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/scenes/{scene_id}</code> - Update scene
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/api/scenes/{scene_id}/content</code> - Update scene content
        </div>
        <div class="endpoint">
            <span class="method patch">PATCH</span> <code>/api/scenes/{scene_id}/reorder</code> - Reorder scene
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span> <code>/api/scenes/{scene_id}</code> - Delete scene
        </div>
        
        <h2>💡 Example Usage</h2>
        <p>1. Create a project: <code>POST /api/projects</code></p>
        <p>2. Add chapters: <code>POST /api/chapters</code></p>
        <p>3. Create scenes: <code>POST /api/scenes</code></p>
        <p>4. Start writing: <code>PUT /api/scenes/{id}/content</code></p>
        
        <h2>✨ Features</h2>
        <ul>
            <li>📊 Automatic word count tracking</li>
            <li>📄 Drag-and-drop reordering for chapters and scenes</li>
            <li>📈 Project progress statistics</li>
            <li>💾 Auto-save functionality</li>
            <li>🏷️ Genre and metadata management</li>
        </ul>
        
        <p><strong>Ready to start writing your novel? Check out the <a href="/api/docs">API documentation</a> to get started!</strong></p>
    </body>
    </html>
    """


@app.get("/api", response_class=HTMLResponse)
async def api_docs():
    """API documentation page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Novel Writing App API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
            .get { background-color: #61affe; }
            .post { background-color: #49cc90; }
            .put { background-color: #fca130; }
            .patch { background-color: #50e3c2; }
            .delete { background-color: #f93e3e; }
            h1 { color: #333; }
            h2 { color: #666; border-bottom: 2px solid #eee; }
        </style>
    </head>
    <body>
        <h1>📚 Novel Writing App API</h1>
        <p>Welcome to the Novel Writing App API! This API helps you manage your novel writing projects, chapters, and scenes.</p>

        <h2>📖 API Documentation</h2>
        <ul>
            <li><a href="/api/docs" target="_blank">Interactive API Documentation (Swagger)</a></li>
            <li><a href="/api/redoc" target="_blank">ReDoc Documentation</a></li>
        </ul>

        <h2>🌐 Web Interface</h2>
        <ul>
            <li><a href="/">Home</a> - Dashboard and project overview</li>
            <li><a href="/projects">Projects</a> - Manage your writing projects</li>
        </ul>

        <h2>🚀 Quick Start Endpoints</h2>

        <h3>Projects</h3>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/projects</code> - Get all projects
        </div>
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/projects</code> - Create a new project
        </div>
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/projects/{project_id}</code> - Get project details
        </div>

        <p><strong>Ready to start writing? Visit the <a href="/">web interface</a> or check out the <a href="/api/docs">API documentation</a>!</strong></p>
    </body>
    </html>
    """